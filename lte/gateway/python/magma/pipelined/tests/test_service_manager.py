"""
Copyright (c) 2019-present, Facebook, Inc.
All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree. An additional grant
of patent rights can be found in the PATENTS file in the same directory.
"""

import unittest
from unittest.mock import MagicMock

from magma.pipelined.app.access_control import AccessControlController
from magma.pipelined.app.arp import ArpController
from lte.protos.mconfig.mconfigs_pb2 import PipelineD
from magma.pipelined.app.dpi import DPIController
from magma.pipelined.app.enforcement import EnforcementController
from magma.pipelined.app.enforcement_stats import EnforcementStatsController
from magma.pipelined.app.inout import INGRESS, EGRESS
from magma.pipelined.app.meter import MeterController
from magma.pipelined.app.meter_stats import MeterStatsController
from magma.pipelined.service_manager import ServiceManager, TableNumException


class ServiceManagerTest(unittest.TestCase):
    def setUp(self):
        magma_service_mock = MagicMock()
        magma_service_mock.mconfig = PipelineD()
        magma_service_mock.mconfig.services.extend(
            [PipelineD.ENFORCEMENT, PipelineD.DPI, PipelineD.METERING])
        magma_service_mock.config = {
            'static_services': ['arpd', 'access_control']
        }
        # Hack since service manager is supposed to be a singleton.
        ServiceManager._instance = None
        self.service_manager = ServiceManager(magma_service_mock)

    def test_get_table_num(self):
        self.assertEqual(self.service_manager.get_table_num(INGRESS), 1)
        self.assertEqual(self.service_manager.get_table_num(EGRESS), 20)
        self.assertEqual(
            self.service_manager.get_table_num(ArpController.APP_NAME), 2)
        self.assertEqual(
            self.service_manager.get_table_num(
                AccessControlController.APP_NAME), 3)
        self.assertEqual(
            self.service_manager.get_table_num(EnforcementController.APP_NAME),
            4)
        self.assertEqual(
            self.service_manager.get_table_num(DPIController.APP_NAME),
            5)
        self.assertEqual(
            self.service_manager.get_table_num(MeterController.APP_NAME),
            6)
        self.assertEqual(
            self.service_manager.get_table_num(MeterStatsController.APP_NAME),
            6)

    def test_get_next_table_num(self):
        self.assertEqual(self.service_manager.get_next_table_num(INGRESS), 2)
        self.assertEqual(
            self.service_manager.get_next_table_num(ArpController.APP_NAME), 3)
        self.assertEqual(
            self.service_manager.get_next_table_num(
                AccessControlController.APP_NAME), 4)
        self.assertEqual(
            self.service_manager.get_next_table_num(
                EnforcementController.APP_NAME),
            5)
        self.assertEqual(
            self.service_manager.get_next_table_num(DPIController.APP_NAME),
            6)
        self.assertEqual(
            self.service_manager.get_next_table_num(MeterController.APP_NAME),
            20)
        self.assertEqual(
            self.service_manager.get_next_table_num(
                MeterStatsController.APP_NAME),
            20)

    def test_is_app_enabled(self):
        self.assertTrue(self.service_manager.is_app_enabled(
            EnforcementController.APP_NAME))
        self.assertTrue(self.service_manager.is_app_enabled(
            DPIController.APP_NAME))
        self.assertTrue(self.service_manager.is_app_enabled(
            MeterController.APP_NAME))
        self.assertTrue(self.service_manager.is_app_enabled(
            MeterStatsController.APP_NAME))
        self.assertTrue(self.service_manager.is_app_enabled(
            EnforcementStatsController.APP_NAME))

        self.assertFalse(
            self.service_manager.is_app_enabled("Random name lol"))

    def test_allocate_scratch_tables(self):
        self.assertEqual(self.service_manager.allocate_scratch_tables(
            EnforcementController.APP_NAME, 1), [21])
        self.assertEqual(self.service_manager.allocate_scratch_tables(
            EnforcementController.APP_NAME, 2), [22, 23])

        # There are a total of 255 tables. First 20 tables are reserved as
        # main tables and 3 scratch tables are allocated above.
        with self.assertRaises(TableNumException):
            self.service_manager.allocate_scratch_tables(
                EnforcementController.APP_NAME, 255 - 20 - 3)

    def test_get_scratch_table_nums(self):
        enforcement_scratch = \
            self.service_manager.allocate_scratch_tables(
                EnforcementController.APP_NAME, 2) + \
            self.service_manager.allocate_scratch_tables(
                EnforcementController.APP_NAME, 3)

        self.assertEqual(self.service_manager.get_scratch_table_nums(
            EnforcementController.APP_NAME), enforcement_scratch)
        self.assertEqual(self.service_manager.get_scratch_table_nums(
            MeterController.APP_NAME), [])

if __name__ == "__main__":
    unittest.main()
