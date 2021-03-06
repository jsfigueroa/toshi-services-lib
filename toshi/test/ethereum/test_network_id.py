import unittest
from toshi.ethereum.tx import (
    add_signature_to_transaction, encode_transaction, decode_transaction,
    DEFAULT_STARTGAS, DEFAULT_GASPRICE, create_transaction,
    is_transaction_signed, calculate_transaction_hash, sign_transaction
)
from toshi.ethereum.utils import data_decoder, data_encoder
from toshi.test.ethereum.parity import FAUCET_PRIVATE_KEY, FAUCET_ADDRESS
from ethereum.transactions import Transaction, UnsignedTransaction
from toshi.utils import parse_int
import rlp

class TestNetworkId(unittest.TestCase):

    def test_tx_network_id(self):

        network_id = 1
        tx = create_transaction(nonce=9, gasprice=20 * 10**9, startgas=21000, to="0x3535353535353535353535353535353535353535", value=10**18, data=b'', network_id=network_id)
        key = data_decoder("0x4646464646464646464646464646464646464646464646464646464646464646")

        self.assertEqual("0xec098504a817c800825208943535353535353535353535353535353535353535880de0b6b3a764000080018080", encode_transaction(tx))
        tx.sign(key, network_id=network_id)

        self.assertEqual(
            "0xf86c098504a817c800825208943535353535353535353535353535353535353535880de0b6b3a76400008025a028ef61340bd939bc2195fe537567866003e1a15d3c71ff63e1590620aa636276a067cbe9d8997f761aecb703304b3800ccf555c9f3dc64214b297fb1966a3b6d83",
            data_encoder(rlp.encode(tx)))

        self.assertEqual(
            (37, 0x28ef61340bd939bc2195fe537567866003e1a15d3c71ff63e1590620aa636276, 0x67cbe9d8997f761aecb703304b3800ccf555c9f3dc64214b297fb1966a3b6d83),
            (tx.v, tx.r, tx.s)
        )

    def test_sign_transaction_with_network_id(self):
        rlp = "0xec831000008504a817c80082520894056db290f8ba3250ca64a45d16284d04bc6f5fbf8502540be40080428080"
        tx = decode_transaction(rlp)
        tx = sign_transaction(tx, FAUCET_PRIVATE_KEY)

        self.assertEqual(data_encoder(tx.sender), FAUCET_ADDRESS)
        # after decoding a transaction, the rlp lib caches the rlp encoding from the given values
        # since the sign_transaction modifies that values, this makes sure the cache isn't used next
        # time the tx is encoded
        self.assertEqual(data_encoder(tx.hash), "0x102234ef30bb90955517ddf92dc7ce39fff7bb4ef760409b984983ad73585bf5",
                         "Incorrect transaction hash after signing")

    def test_should_agree_with_vitalik(self):
        """Based on https://github.com/ethereum/tests/blob/develop/TransactionTests/EIP155/ttTransactionTestEip155VitaliksTests.json"""

        def test_vector(name, vector):
            if 'transaction' not in vector:
                return # TODO: process rlp tests
            transaction = vector['transaction']
            tx = create_transaction(nonce=parse_int(transaction['nonce']), gasprice=parse_int(transaction['gasPrice']), startgas=parse_int(transaction['gasLimit']),
                                    to=transaction['to'], value=parse_int(transaction['value']), data=data_decoder(transaction['data']),
                                    v=parse_int(transaction['v']), r=parse_int(transaction['r']), s=parse_int(transaction['s']))
            self.assertEqual(data_encoder(tx.sender), "0x{}".format(vector['sender']), name)
            self.assertEqual(calculate_transaction_hash(tx), "0x{}".format(vector['hash']), name)
            self.assertEqual(encode_transaction(tx), vector['rlp'], name)

            # test decode transaction -> encode transaction round trip
            tx = decode_transaction(vector['rlp'])
            self.assertEqual(encode_transaction(tx), vector['rlp'], name)

        vectors = {
            "Vitalik_1" : {
                "blocknumber" : "2675000",
                "hash" : "b1e2188bc490908a78184e4818dca53684167507417fdb4c09c2d64d32a9896a",
                "rlp" : "0xf864808504a817c800825208943535353535353535353535353535353535353535808025a0044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116da0044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d",
                "sender" : "f0f6f18bca1b28cd68e4357452947e021241e9ce",
                "transaction" : {
                    "data" : "",
                    "gasLimit" : "0x5208",
                    "gasPrice" : "0x04a817c800",
                    "nonce" : "0x00",
                    "r" : "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d",
                    "s" : "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d",
                    "to" : "0x3535353535353535353535353535353535353535",
                    "v" : "0x25",
                    "value" : "0x00"
                }
            },
            "Vitalik_10" : {
                "blocknumber" : "2675000",
                "hash" : "588df025c4c2d757d3e314bd3dfbfe352687324e6b8557ad1731585e96928aed",
                "rlp" : "0xf867088504a817c8088302e2489435353535353535353535353535353535353535358202008025a064b1702d9298fee62dfeccc57d322a463ad55ca201256d01f62b45b2e1c21c12a064b1702d9298fee62dfeccc57d322a463ad55ca201256d01f62b45b2e1c21c10",
                "sender" : "9bddad43f934d313c2b79ca28a432dd2b7281029",
                "transaction" : {
                    "data" : "",
                    "gasLimit" : "0x02e248",
                    "gasPrice" : "0x04a817c808",
                    "nonce" : "0x08",
                    "r" : "0x64b1702d9298fee62dfeccc57d322a463ad55ca201256d01f62b45b2e1c21c12",
                    "s" : "0x64b1702d9298fee62dfeccc57d322a463ad55ca201256d01f62b45b2e1c21c10",
                    "to" : "0x3535353535353535353535353535353535353535",
                    "v" : "0x25",
                    "value" : "0x0200"
                }
            },
            "Vitalik_11" : {
                "blocknumber" : "2675000",
                "hash" : "f39c7dac06a9f3abf09faf5e30439a349d3717611b3ed337cd52b0d192bc72da",
                "rlp" : "0xf867098504a817c809830334509435353535353535353535353535353535353535358202d98025a052f8f61201b2b11a78d6e866abc9c3db2ae8631fa656bfe5cb53668255367afba052f8f61201b2b11a78d6e866abc9c3db2ae8631fa656bfe5cb53668255367afb",
                "sender" : "3c24d7329e92f84f08556ceb6df1cdb0104ca49f",
                "transaction" : {
                    "data" : "",
                    "gasLimit" : "0x033450",
                    "gasPrice" : "0x04a817c809",
                    "nonce" : "0x09",
                    "r" : "0x52f8f61201b2b11a78d6e866abc9c3db2ae8631fa656bfe5cb53668255367afb",
                    "s" : "0x52f8f61201b2b11a78d6e866abc9c3db2ae8631fa656bfe5cb53668255367afb",
                    "to" : "0x3535353535353535353535353535353535353535",
                    "v" : "0x25",
                    "value" : "0x02d9"
                }
            },
            "Vitalik_12" : {
                "blocknumber" : "2675000",
                "hash" : "db38325f4c7a9917a611fd09694492c23b0ec357a68ab5cbf905fc9757b9919a",
                "rlp" : "0xf8610e80830493e080809560f2ff61000080610011600039610011565b6000f31ca0a310f4d0b26207db76ba4e1e6e7cf1857ee3aa8559bcbc399a6b09bfea2d30b4a06dff38c645a1486651a717ddf3daccb4fd9a630871ecea0758ddfcf2774f9bc6",
                "sender" : "874b54a8bd152966d63f706bae1ffeb0411921e5",
                "transaction" : {
                    "data" : "0x60f2ff61000080610011600039610011565b6000f3",
                    "gasLimit" : "0x0493e0",
                    "gasPrice" : "0x00",
                    "nonce" : "0x0e",
                    "r" : "0xa310f4d0b26207db76ba4e1e6e7cf1857ee3aa8559bcbc399a6b09bfea2d30b4",
                    "s" : "0x6dff38c645a1486651a717ddf3daccb4fd9a630871ecea0758ddfcf2774f9bc6",
                    "to" : "",
                    "v" : "0x1c",
                    "value" : "0x00"
                }
            },
            "Vitalik_13" : {
                "blocknumber" : "2675000",
                "hash" : "278608eba8465230d0552c8df9fbcc6fc35d2350f4feb0e49a399b2adab37e39",
                "rlp" : "0xf8660f80830493e09400000000000000000000000000000000000000c08086646f6e6b65791ba09f00c6da4f2e4b5f3316e70c7669f9df71fa21d533afa63450065731132ba7b6a03886c27a8b3515ab9e2e04492f8214718621421e92d3b6954d9e3fb409ead788",
                "sender" : "874b54a8bd152966d63f706bae1ffeb0411921e5",
                "transaction" : {
                    "data" : "0x646f6e6b6579",
                    "gasLimit" : "0x0493e0",
                    "gasPrice" : "0x00",
                    "nonce" : "0x0f",
                    "r" : "0x9f00c6da4f2e4b5f3316e70c7669f9df71fa21d533afa63450065731132ba7b6",
                    "s" : "0x3886c27a8b3515ab9e2e04492f8214718621421e92d3b6954d9e3fb409ead788",
                    "to" : "0x00000000000000000000000000000000000000c0",
                    "v" : "0x1b",
                    "value" : "0x00"
                }
            },
            "Vitalik_14" : {
                "blocknumber" : "2675000",
                "hash" : "d9a26fff8704b137b592b07b64a86eac555dc347c87ae7fe1d2fe824d12427e5",
                "rlp" : "0xf8610f80830493e080019560f3ff61000080610011600039610011565b6000f31ba0af2944b645e280a35789aacfce7e16a8d57b43a0076dfd564bdc0395e3576324a05272a0013f198713128bb0e3da43bb03ec7224c5509d4cabbe39fd31c36b5786",
                "sender" : "874b54a8bd152966d63f706bae1ffeb0411921e5",
                "transaction" : {
                    "data" : "0x60f3ff61000080610011600039610011565b6000f3",
                    "gasLimit" : "0x0493e0",
                    "gasPrice" : "0x00",
                    "nonce" : "0x0f",
                    "r" : "0xaf2944b645e280a35789aacfce7e16a8d57b43a0076dfd564bdc0395e3576324",
                    "s" : "0x5272a0013f198713128bb0e3da43bb03ec7224c5509d4cabbe39fd31c36b5786",
                    "to" : "",
                    "v" : "0x1b",
                    "value" : "0x01"
                }
            },
            "Vitalik_15" : {
                "blocknumber" : "2675000",
                "rlp" : "0xf8651280830493e094000000000000000000000000000000000000000180856d6f6f736529a0376d0277dd3a2a9229dbcb5530b532c7e4cb0f821e0ca27d9acb940970d500d8a00ab2798f9d9c2f7551eb29d56878f8e342b45ca45f413b0fcba793d094f36f2b"
            },
            "Vitalik_16" : {
                "blocknumber" : "2675000",
                "rlp" : "0xf8651380830493e094000000000000000000000000000000000000001280856d6f6f73652aa0d0e340578f9d733986f6a55c5401953c90f7ccd46fe72d5588592dd9cbdf1e03a001d8d63149bd986f363084ac064e8387850d80e5238cc16ed4d30fd0a5af7261"
            },
            "Vitalik_17" : {
                "blocknumber" : "2675000",
                "rlp" : "0xf8651480830493e094000000000000000000000000000000000000002280856d6f6f73652aa04bc84887af29d2b159ee290dee793bdba34079428f48699e9fc92a7e12d4aeafa063b9d78c5a36f96454fe2d5c1eb7c0264f6273afdc0ba28dd9a8f00eadaf7476"
            },
            "Vitalik_2" : {
                "blocknumber" : "2675000",
                "hash" : "e62703f43b6f10d42b520941898bf710ebb66dba9df81702702b6d9bf23fef1b",
                "rlp" : "0xf864018504a817c80182a410943535353535353535353535353535353535353535018025a0489efdaa54c0f20c7adf612882df0950f5a951637e0307cdcb4c672f298b8bcaa0489efdaa54c0f20c7adf612882df0950f5a951637e0307cdcb4c672f298b8bc6",
                "sender" : "23ef145a395ea3fa3deb533b8a9e1b4c6c25d112",
                "transaction" : {
                    "data" : "",
                    "gasLimit" : "0xa410",
                    "gasPrice" : "0x04a817c801",
                    "nonce" : "0x01",
                    "r" : "0x489efdaa54c0f20c7adf612882df0950f5a951637e0307cdcb4c672f298b8bca",
                    "s" : "0x489efdaa54c0f20c7adf612882df0950f5a951637e0307cdcb4c672f298b8bc6",
                    "to" : "0x3535353535353535353535353535353535353535",
                    "v" : "0x25",
                    "value" : "0x01"
                }
            },
            "Vitalik_3" : {
                "blocknumber" : "2675000",
                "hash" : "1f621d7d8804723ab6fec606e504cc893ad4fe4a545d45f499caaf16a61d86dd",
                "rlp" : "0xf864028504a817c80282f618943535353535353535353535353535353535353535088025a02d7c5bef027816a800da1736444fb58a807ef4c9603b7848673f7e3a68eb14a5a02d7c5bef027816a800da1736444fb58a807ef4c9603b7848673f7e3a68eb14a5",
                "sender" : "2e485e0c23b4c3c542628a5f672eeab0ad4888be",
                "transaction" : {
                    "data" : "",
                    "gasLimit" : "0xf618",
                    "gasPrice" : "0x04a817c802",
                    "nonce" : "0x02",
                    "r" : "0x2d7c5bef027816a800da1736444fb58a807ef4c9603b7848673f7e3a68eb14a5",
                    "s" : "0x2d7c5bef027816a800da1736444fb58a807ef4c9603b7848673f7e3a68eb14a5",
                    "to" : "0x3535353535353535353535353535353535353535",
                    "v" : "0x25",
                    "value" : "0x08"
                }
            },
            "Vitalik_4" : {
                "blocknumber" : "2675000",
                "hash" : "99b6455776b1988840d0074c23772cb6b323eb32c5011e4a3a1d06d27b2eb425",
                "rlp" : "0xf865038504a817c803830148209435353535353535353535353535353535353535351b8025a02a80e1ef1d7842f27f2e6be0972bb708b9a135c38860dbe73c27c3486c34f4e0a02a80e1ef1d7842f27f2e6be0972bb708b9a135c38860dbe73c27c3486c34f4de",
                "sender" : "82a88539669a3fd524d669e858935de5e5410cf0",
                "transaction" : {
                    "data" : "",
                    "gasLimit" : "0x014820",
                    "gasPrice" : "0x04a817c803",
                    "nonce" : "0x03",
                    "r" : "0x2a80e1ef1d7842f27f2e6be0972bb708b9a135c38860dbe73c27c3486c34f4e0",
                    "s" : "0x2a80e1ef1d7842f27f2e6be0972bb708b9a135c38860dbe73c27c3486c34f4de",
                    "to" : "0x3535353535353535353535353535353535353535",
                    "v" : "0x25",
                    "value" : "0x1b"
                }
            },
            "Vitalik_5" : {
                "blocknumber" : "2675000",
                "hash" : "0b2b499d5a3e729bcc197e1a00f922d80890472299dd1c648988eb08b5b1ff0a",
                "rlp" : "0xf865048504a817c80483019a28943535353535353535353535353535353535353535408025a013600b294191fc92924bb3ce4b969c1e7e2bab8f4c93c3fc6d0a51733df3c063a013600b294191fc92924bb3ce4b969c1e7e2bab8f4c93c3fc6d0a51733df3c060",
                "sender" : "f9358f2538fd5ccfeb848b64a96b743fcc930554",
                "transaction" : {
                    "data" : "",
                    "gasLimit" : "0x019a28",
                    "gasPrice" : "0x04a817c804",
                    "nonce" : "0x04",
                    "r" : "0x13600b294191fc92924bb3ce4b969c1e7e2bab8f4c93c3fc6d0a51733df3c063",
                    "s" : "0x13600b294191fc92924bb3ce4b969c1e7e2bab8f4c93c3fc6d0a51733df3c060",
                    "to" : "0x3535353535353535353535353535353535353535",
                    "v" : "0x25",
                    "value" : "0x40"
                }
            },
            "Vitalik_6" : {
                "blocknumber" : "2675000",
                "hash" : "99a214f26aaf2804d84367ac8f33ff74b3a94e68baf820668f3641819ced1216",
                "rlp" : "0xf865058504a817c8058301ec309435353535353535353535353535353535353535357d8025a04eebf77a833b30520287ddd9478ff51abbdffa30aa90a8d655dba0e8a79ce0c1a04eebf77a833b30520287ddd9478ff51abbdffa30aa90a8d655dba0e8a79ce0c1",
                "sender" : "a8f7aba377317440bc5b26198a363ad22af1f3a4",
                "transaction" : {
                    "data" : "",
                    "gasLimit" : "0x01ec30",
                    "gasPrice" : "0x04a817c805",
                    "nonce" : "0x05",
                    "r" : "0x4eebf77a833b30520287ddd9478ff51abbdffa30aa90a8d655dba0e8a79ce0c1",
                    "s" : "0x4eebf77a833b30520287ddd9478ff51abbdffa30aa90a8d655dba0e8a79ce0c1",
                    "to" : "0x3535353535353535353535353535353535353535",
                    "v" : "0x25",
                    "value" : "0x7d"
                }
            },
            "Vitalik_7" : {
                "blocknumber" : "2675000",
                "hash" : "99a214f26aaf2804d84367ac8f33ff74b3a94e68baf820668f3641819ced1216",
                "rlp" : "0xf865058504a817c8058301ec309435353535353535353535353535353535353535357d8025a04eebf77a833b30520287ddd9478ff51abbdffa30aa90a8d655dba0e8a79ce0c1a04eebf77a833b30520287ddd9478ff51abbdffa30aa90a8d655dba0e8a79ce0c1",
                "sender" : "a8f7aba377317440bc5b26198a363ad22af1f3a4",
                "transaction" : {
                    "data" : "",
                    "gasLimit" : "0x01ec30",
                    "gasPrice" : "0x04a817c805",
                    "nonce" : "0x05",
                    "r" : "0x4eebf77a833b30520287ddd9478ff51abbdffa30aa90a8d655dba0e8a79ce0c1",
                    "s" : "0x4eebf77a833b30520287ddd9478ff51abbdffa30aa90a8d655dba0e8a79ce0c1",
                    "to" : "0x3535353535353535353535353535353535353535",
                    "v" : "0x25",
                    "value" : "0x7d"
                }
            },
            "Vitalik_8" : {
                "blocknumber" : "2675000",
                "hash" : "4ed0b4b20536cce62389c6b95ff6a517489b6045efdefeabb4ecf8707d99e15d",
                "rlp" : "0xf866068504a817c80683023e3894353535353535353535353535353535353535353581d88025a06455bf8ea6e7463a1046a0b52804526e119b4bf5136279614e0b1e8e296a4e2fa06455bf8ea6e7463a1046a0b52804526e119b4bf5136279614e0b1e8e296a4e2d",
                "sender" : "f1f571dc362a0e5b2696b8e775f8491d3e50de35",
                "transaction" : {
                    "data" : "",
                    "gasLimit" : "0x023e38",
                    "gasPrice" : "0x04a817c806",
                    "nonce" : "0x06",
                    "r" : "0x6455bf8ea6e7463a1046a0b52804526e119b4bf5136279614e0b1e8e296a4e2f",
                    "s" : "0x6455bf8ea6e7463a1046a0b52804526e119b4bf5136279614e0b1e8e296a4e2d",
                    "to" : "0x3535353535353535353535353535353535353535",
                    "v" : "0x25",
                    "value" : "0xd8"
                }
            },
            "Vitalik_9" : {
                "blocknumber" : "2675000",
                "hash" : "a40eb7000de852898a385a19312284bb06f6a9b5d8d03e0b8fb5df2f07f9fe94",
                "rlp" : "0xf867078504a817c807830290409435353535353535353535353535353535353535358201578025a052f1a9b320cab38e5da8a8f97989383aab0a49165fc91c737310e4f7e9821021a052f1a9b320cab38e5da8a8f97989383aab0a49165fc91c737310e4f7e9821021",
                "sender" : "d37922162ab7cea97c97a87551ed02c9a38b7332",
                "transaction" : {
                    "data" : "",
                    "gasLimit" : "0x029040",
                    "gasPrice" : "0x04a817c807",
                    "nonce" : "0x07",
                    "r" : "0x52f1a9b320cab38e5da8a8f97989383aab0a49165fc91c737310e4f7e9821021",
                    "s" : "0x52f1a9b320cab38e5da8a8f97989383aab0a49165fc91c737310e4f7e9821021",
                    "to" : "0x3535353535353535353535353535353535353535",
                    "v" : "0x25",
                    "value" : "0x0157"
                }
            }
        }

        for name, vector in vectors.items():
            test_vector(name, vector)
