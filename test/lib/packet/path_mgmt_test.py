# Copyright 2015 ETH Zurich
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
:mod:`lib_packet_path_mgmt_test` --- lib.packet.path_mgmt tests
=====================================================
"""
# Stdlib
from unittest.mock import patch, call

# External packages
import nose
import nose.tools as ntools

# SCION
from lib.errors import SCIONParseError
from lib.packet.path_mgmt import (
    IFStateInfo,
    IFStatePayload,
    IFStateRequest,
    PathSegmentInfo,
    PathSegmentRecords,
    parse_pathmgmt_payload,
)
from test.testcommon import (
    assert_these_calls,
    create_mock,
)


class TestPathSegmentInfoParse(object):
    """
    Unit tests for lib.packet.path_mgmt.PathSegmentInfo._parse
    """
    @patch("lib.packet.path_mgmt.ISD_AS", autospec=True)
    @patch("lib.packet.path_mgmt.Raw", autospec=True)
    def test(self, raw, isd_as):
        inst = PathSegmentInfo()
        data = create_mock(["pop"])
        data.pop.side_effect = ("seg type", "src isd-as", "dst isd-as")
        raw.return_value = data
        isd_as.side_effect = lambda x: x
        # Call
        inst._parse("data")
        # Tests
        raw.assert_called_once_with("data", inst.NAME, inst.LEN)
        ntools.eq_(inst.seg_type, "seg type")
        ntools.eq_(inst.src_ia, "src isd-as")
        ntools.eq_(inst.dst_ia, "dst isd-as")


class TestPathSegmentInfoPack(object):
    """
    Unit tests for lib.packet.path_mgmt.PathSegmentInfo.pack
    """
    def test_basic(self):
        inst = PathSegmentInfo()
        inst.seg_type = 0x0e
        inst.src_ia = create_mock(["pack"])
        inst.src_ia.pack.return_value = b"src isd-as"
        inst.dst_ia = create_mock(["pack"])
        inst.dst_ia.pack.return_value = b"dst isd-as"
        expected = b"".join([bytes([0x0e]), b"src isd-as", b"dst isd-as"])
        # Call
        ntools.eq_(inst.pack(), expected)


class TestPathSegmentRecordsParse(object):
    """
    Unit tests for lib.packet.path_mgmt.PathSegmentRecords._parse
    """
    @patch("lib.packet.path_mgmt.PathSegment", autospec=True)
    @patch("lib.packet.path_mgmt.Raw", autospec=True)
    def test(self, raw, path_seg):
        inst = PathSegmentRecords()
        inst.NAME = "PathSegmentRecords"
        data = create_mock(["__bool__", "pop", "get"])
        data.__bool__.side_effect = True, True, True, False
        data.pop.side_effect = 1, None, 1, None, 2, None
        data.get.side_effect = "pcb1_0", "pcb1_1", "pcb2_0"
        raw.return_value = data
        path_seg.side_effect = lambda x: x
        # Call
        inst._parse("data")
        # Tests
        raw.assert_called_once_with("data", inst.NAME, inst.MIN_LEN, min_=True)
        assert_these_calls(path_seg, [
            call("pcb1_0"), call("pcb1_1"), call("pcb2_0")])
        ntools.eq_(dict(inst.pcbs), {1: ["pcb1_0", "pcb1_1"], 2: ["pcb2_0"]})


class TestPathSegmentRecordsPack(object):
    """
    Unit tests for lib.packet.path_mgmt.PathSegmentRecords.pack
    """
    def _mk_seg(self, val):
        seg = create_mock(['__len__', 'pack'])
        seg.__len__.return_value = len(val)
        seg.pack.return_value = val
        return seg

    def test(self):
        inst = PathSegmentRecords()
        inst.pcbs = {
            1: [self._mk_seg(b"pcb1_0"), self._mk_seg(b"pcb1_1")],
            2: [self._mk_seg(b"pcb2_0")],
        }
        expected = [
            b"\x01pcb1_0", b"\x01pcb1_1", b"\x02pcb2_0"
        ]
        # Call
        ret = inst.pack()
        # Tests
        ntools.eq_(len(ret), len(b"".join(expected)))
        for b in expected:
            ntools.assert_in(b, ret)


class TestPathSegmentRecordsLen(object):
    """
    Unit tests for lib.packet.path_mgmt.PathSegmentRecords.__len__
    """
    def test(self):
        inst = PathSegmentRecords()
        inst.pcbs = {1: ['1', '22', '333', '4444'], 2: ['55555'], 3: ['666666']}
        # Call
        ntools.eq_(len(inst), 2 + 3 + 4 + 5 + 6 + 7)


class TestIFStateInfoParse(object):
    """
    Unit tests for lib.packet.path_mgmt.IFStateInfo._parse
    """
    @patch("lib.packet.path_mgmt.RevocationInfo", autospec=True)
    @patch("lib.packet.path_mgmt.Raw", autospec=True)
    def test(self, raw, rev_info_cls):
        inst = IFStateInfo()
        data = create_mock(["pop"])
        data.pop.side_effect = bytes.fromhex("00001111"), "rev info"
        raw.return_value = data
        # Call
        inst._parse("data")
        # Tests
        raw.assert_called_once_with("data", inst.NAME, inst.LEN)
        ntools.eq_(inst.if_id, 0x0000)
        ntools.eq_(inst.state, 0x1111)
        rev_info_cls.assert_called_once_with("rev info")
        ntools.eq_(inst.rev_info, rev_info_cls.return_value)


class TestIFStateInfoPack(object):
    """
    Unit tests for lib.packet.path_mgmt.IFStateInfo.pack
    """
    def test(self):
        inst = IFStateInfo()
        inst.if_id = 0x0000
        inst.state = 0x1111
        inst.rev_info = create_mock(["pack"])
        inst.rev_info.pack.return_value = b"rev token"
        expected = bytes.fromhex("00001111") + b"rev token"
        # Call
        ntools.eq_(inst.pack(), expected)


class TestIFStatePayloadParse(object):
    """
    Unit tests for lib.packet.path_mgmt.IFStatePayload._parse
    """
    @patch("lib.packet.path_mgmt.IFStateInfo", autospec=True)
    @patch("lib.packet.path_mgmt.Raw", autospec=True)
    def test(self, raw, if_state_info):
        inst = IFStatePayload()
        data = create_mock(["__len__", "pop"])
        data.__len__.side_effect = 3, 2, 1, 0
        raw_state_infos = ["if_state%d" % i for i in range(3)]
        data.pop.side_effect = raw_state_infos
        raw.return_value = data
        state_infos = ["if state info %d" % i for i in range(3)]
        if_state_info.side_effect = state_infos
        # Call
        inst._parse("data")
        # Tests
        raw.assert_called_once_with("data", inst.NAME, inst.MIN_LEN, min_=True)
        assert_these_calls(if_state_info, [call(i) for i in raw_state_infos])
        ntools.eq_(inst.ifstate_infos, state_infos)


class TestIFStatePayloadPack(object):
    """
    Unit tests for lib.packet.path_mgmt.IFStatePayload.pack
    """
    def test(self):
        inst = IFStatePayload()
        for i in range(3):
            info = create_mock(["pack"])
            info.pack.return_value = bytes("info%d" % i, "ascii")
            inst.ifstate_infos.append(info)
        expected = b"info0" b"info1" b"info2"
        # Call
        ntools.eq_(inst.pack(), expected)


class TestIFStateRequestParse(object):
    """
    Unit tests for lib.packet.path_mgmt.IFStateRequest._parse
    """
    @patch("lib.packet.path_mgmt.IFStateInfo", autospec=True)
    @patch("lib.packet.path_mgmt.Raw", autospec=True)
    def test(self, raw, if_state_info):
        inst = IFStateRequest()
        data = create_mock(["__len__", "pop"])
        data.pop.return_value = bytes.fromhex("1234")
        raw.return_value = data
        # Call
        inst._parse("data")
        # Tests
        raw.assert_called_once_with("data", inst.NAME, inst.LEN)
        ntools.eq_(inst.if_id, 0x1234)


class TestIFStateRequestPack(object):
    """
    Unit tests for lib.packet.path_mgmt.IFStateRequest.pack
    """
    def test(self):
        inst = IFStateRequest()
        inst.if_id = 0x1234
        # Call
        ntools.eq_(inst.pack(), bytes.fromhex("1234"))


class TestParsePathMgmtPayload(object):
    """
    Unit tests for lib.packet.path_mgmt.parse_pathmgmt_payload
    """
    @patch("lib.packet.path_mgmt._TYPE_MAP", new_callable=dict)
    def _check_supported(self, type_, type_map):
        type_map[0] = create_mock(), 20
        type_map[1] = create_mock(), None
        handler, len_ = type_map[type_]
        data = create_mock(["pop"])
        # Call
        ntools.eq_(parse_pathmgmt_payload(type_, data), handler.return_value)
        # Tests
        data.pop.assert_called_once_with(len_)
        handler.assert_called_once_with(data.pop.return_value)

    def test_supported(self):
        for type_ in (0, 1):
            yield self._check_supported, type_

    def test_unsupported(self):
        # Call
        ntools.assert_raises(SCIONParseError, parse_pathmgmt_payload,
                             "unknown type", "data")


if __name__ == "__main__":
    nose.run(defaultTest=__name__)