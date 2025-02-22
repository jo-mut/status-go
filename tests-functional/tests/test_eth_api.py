import pytest

from test_cases import EthRpcTestCase


def validate_header(header, block_number, block_hash):
    assert header["number"] == block_number
    assert header["hash"] == block_hash


def validate_block(block, block_number, block_hash, expected_tx_hash):
    validate_header(block["header"], block_number, block_hash)
    tx_hashes = [tx["hash"] for tx in block["transactions"]]
    assert expected_tx_hash in tx_hashes


def validate_transaction(tx, tx_hash):
    assert tx["tx"]["hash"] == tx_hash


def validate_receipt(receipt, tx_hash, block_number, block_hash):
    assert receipt["transactionHash"] == tx_hash
    assert receipt["blockNumber"] == block_number
    assert receipt["blockHash"] == block_hash


@pytest.mark.rpc
@pytest.mark.ethclient
class TestEth(EthRpcTestCase):

    def test_block_number(self):
        self.rpc_client.rpc_valid_request("ethclient_blockNumber", [self.network_id])

    def test_suggest_gas_price(self):
        self.rpc_client.rpc_valid_request("ethclient_suggestGasPrice", [self.network_id])

    def test_header_by_number(self, tx_data):
        response = self.rpc_client.rpc_valid_request("ethclient_headerByNumber", [self.network_id, tx_data.block_number])
        validate_header(response.json()["result"], tx_data.block_number, tx_data.block_hash)

    def test_block_by_number(self, tx_data):
        response = self.rpc_client.rpc_valid_request("ethclient_blockByNumber", [self.network_id, tx_data.block_number])
        validate_block(
            response.json()["result"],
            tx_data.block_number,
            tx_data.block_hash,
            tx_data.tx_hash,
        )

    def test_header_by_hash(self, tx_data):
        response = self.rpc_client.rpc_valid_request("ethclient_headerByHash", [self.network_id, tx_data.block_hash])
        validate_header(response.json()["result"], tx_data.block_number, tx_data.block_hash)

    def test_block_by_hash(self, tx_data):
        response = self.rpc_client.rpc_valid_request("ethclient_blockByHash", [self.network_id, tx_data.block_hash])
        validate_block(
            response.json()["result"],
            tx_data.block_number,
            tx_data.block_hash,
            tx_data.tx_hash,
        )

    def test_transaction_by_hash(self, tx_data):
        response = self.rpc_client.rpc_valid_request("ethclient_transactionByHash", [self.network_id, tx_data.tx_hash])
        validate_transaction(response.json()["result"], tx_data.tx_hash)

    def test_transaction_receipt(self, tx_data):
        response = self.rpc_client.rpc_valid_request("ethclient_transactionReceipt", [self.network_id, tx_data.tx_hash])
        validate_receipt(
            response.json()["result"],
            tx_data.tx_hash,
            tx_data.block_number,
            tx_data.block_hash,
        )
