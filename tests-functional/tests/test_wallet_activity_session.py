import json
import random
from utils import wallet_utils
import pytest

from resources.constants import user_1
from test_cases import StatusBackendTestCase
from clients.signals import SignalType

EventActivityFilteringDone = "wallet-activity-filtering-done"
EventActivityFilteringUpdate = "wallet-activity-filtering-entries-updated"
EventActivitySessionUpdated = "wallet-activity-session-updated"


def validate_entry(entry, tx_data):
    assert entry["transactions"][0]["chainId"] == tx_data["tx_status"]["chainId"]
    assert entry["transactions"][0]["hash"] == tx_data["tx_status"]["hash"]


@pytest.mark.wallet
@pytest.mark.rpc
class TestWalletActivitySession(StatusBackendTestCase):
    await_signals = [
        SignalType.NODE_LOGIN.value,
        "wallet",
        "wallet.suggested.routes",
        "wallet.router.sign-transactions",
        "wallet.router.sending-transactions-started",
        "wallet.transaction.status-changed",
        "wallet.router.transactions-sent",
    ]

    def setup_method(self):
        self.request_id = str(random.randint(1, 8888))

    def test_wallet_start_activity_filter_session(self):
        tx_data = []  # (routes, build_tx, tx_signatures, tx_status)
        # Set up a transactions for account before starting session
        tx_data.append(wallet_utils.send_router_transaction(self.rpc_client))

        # Start activity session
        method = "wallet_startActivityFilterSessionV2"
        params = [
            [user_1.address],
            [self.network_id],
            {
                "period": {"startTimestamp": 0, "endTimestamp": 0},
                "types": [],
                "statuses": [],
                "counterpartyAddresses": [],
                "assets": [],
                "collectibles": [],
                "filterOutAssets": False,
                "filterOutCollectibles": False,
            },
            10,
        ]
        self.rpc_client.prepare_wait_for_signal(
            "wallet",
            1,
            lambda signal: signal["event"]["type"] == EventActivityFilteringDone,
        )
        response = self.rpc_client.rpc_valid_request(method, params, self.request_id)
        event_response = self.rpc_client.wait_for_signal("wallet", timeout=10)["event"]

        # Check response
        sessionID = int(response.json()["result"])
        assert sessionID > 0

        # Check response event
        assert int(event_response["requestId"]) == sessionID
        message = json.loads(event_response["message"].replace("'", '"'))
        assert int(message["errorCode"]) == 1
        assert len(message["activities"]) > 0  # Should have at least 1 entry
        # First activity entry should match last sent transaction
        validate_entry(message["activities"][0], tx_data[-1])

        # Trigger new transaction
        self.rpc_client.prepare_wait_for_signal(
            "wallet",
            1,
            lambda signal: signal["event"]["type"] == EventActivitySessionUpdated and signal["event"]["requestId"] == sessionID,
        )
        tx_data.append(wallet_utils.send_router_transaction(self.rpc_client))
        print(tx_data[-1])
        event_response = self.rpc_client.wait_for_signal("wallet", timeout=10)["event"]

        # Check response event
        assert int(event_response["requestId"]) == sessionID
        message = json.loads(event_response["message"].replace("'", '"'))
        assert message["hasNewOnTop"]  # New entries reported

        # Reset activity session
        method = "wallet_resetActivityFilterSession"
        params = [sessionID, 10]
        self.rpc_client.prepare_wait_for_signal(
            "wallet",
            1,
            lambda signal: signal["event"]["type"] == EventActivityFilteringDone and signal["event"]["requestId"] == sessionID,
        )
        response = self.rpc_client.rpc_valid_request(method, params, self.request_id)
        event_response = self.rpc_client.wait_for_signal("wallet", timeout=10)["event"]

        # Check response event
        assert int(event_response["requestId"]) == sessionID
        message = json.loads(event_response["message"].replace("'", '"'))
        assert int(message["errorCode"]) == 1
        assert len(message["activities"]) > 1  # Should have at least 2 entries

        # First activity entry should match last sent transaction
        validate_entry(message["activities"][0], tx_data[-1])

        # Second activity entry should match second to last sent transaction
        validate_entry(message["activities"][1], tx_data[-2])
