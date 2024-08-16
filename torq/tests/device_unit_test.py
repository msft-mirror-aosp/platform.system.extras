#
# Copyright (C) 2024 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import unittest
import os
import subprocess
from unittest import mock
from device import AdbDevice

MOCK_DEVICE_SERIAL = "mock-device-serial"
MOCK_DEVICE_SERIAL2 = "mock-device-serial2"
MOCK_FAILURE = "Mock failure."


class DeviceUnitTest(unittest.TestCase):

  def generate_adb_devices_result(self, devices, adb_started=True):
    devices = [device.encode('utf-8') for device in devices]
    stdout_string = b'List of devices attached\n'
    if not adb_started:
      stdout_string = (b'* daemon not running; starting now at tcp:1234\n'
                       b'* daemon started successfully\n') + stdout_string
    if len(devices) > 0:
      stdout_string += b'\tdevice\n'.join(devices) + b'\tdevice\n'
      stdout_string += b'\n'
    return subprocess.CompletedProcess(args=['adb', 'devices'], returncode=0,
                                       stdout=stdout_string)

  @mock.patch.object(subprocess, "run", autospec=True)
  def test_get_adb_devices_returns_devices(self, mock_subprocess_run):
    mock_subprocess_run.return_value = (
        self.generate_adb_devices_result([MOCK_DEVICE_SERIAL,
                                          MOCK_DEVICE_SERIAL2]))
    adbDevice = AdbDevice(None)

    devices, error = adbDevice.get_adb_devices()

    self.assertEqual(len(devices), 2)
    self.assertEqual(devices[0], MOCK_DEVICE_SERIAL)
    self.assertEqual(devices[1], MOCK_DEVICE_SERIAL2)
    self.assertEqual(error, None)

  @mock.patch.object(subprocess, "run", autospec=True)
  def test_get_adb_devices_returns_devices_and_adb_not_started(self,
      mock_subprocess_run):
    mock_subprocess_run.return_value = (
        self.generate_adb_devices_result([MOCK_DEVICE_SERIAL,
                                          MOCK_DEVICE_SERIAL2], False))
    adbDevice = AdbDevice(None)

    devices, error = adbDevice.get_adb_devices()

    self.assertEqual(len(devices), 2)
    self.assertEqual(devices[0], MOCK_DEVICE_SERIAL)
    self.assertEqual(devices[1], MOCK_DEVICE_SERIAL2)
    self.assertEqual(error, None)

  @mock.patch.object(subprocess, "run", autospec=True)
  def test_get_adb_devices_returns_no_device(self, mock_subprocess_run):
    mock_subprocess_run.return_value = self.generate_adb_devices_result([])
    adbDevice = AdbDevice(None)

    devices, error = adbDevice.get_adb_devices()

    self.assertEqual(devices, [])
    self.assertEqual(error, None)

  @mock.patch.object(subprocess, "run", autospec=True)
  def test_get_adb_devices_returns_no_device_and_adb_not_started(self,
      mock_subprocess_run):
    mock_subprocess_run.return_value = (
        self.generate_adb_devices_result([], False))
    adbDevice = AdbDevice(None)

    devices, error = adbDevice.get_adb_devices()

    self.assertEqual(devices, [])
    self.assertEqual(error, None)

  @mock.patch.object(subprocess, "run", autospec=True)
  def test_get_adb_devices_command_failure_error(self, mock_subprocess_run):
    mock_subprocess_run.side_effect = Exception(MOCK_FAILURE)
    adbDevice = AdbDevice(None)

    devices, error = adbDevice.get_adb_devices()

    self.assertEqual(devices, None)
    self.assertEqual(error.message, ("Command 'adb devices' failed. %s"
                                     % MOCK_FAILURE))
    self.assertEqual(error.suggestion, None)

  @mock.patch.object(subprocess, "run", autospec=True)
  def test_check_device_connection_serial_arg_in_devices(self,
      mock_subprocess_run):
    mock_subprocess_run.return_value = (
        self.generate_adb_devices_result([MOCK_DEVICE_SERIAL]))
    adbDevice = AdbDevice(MOCK_DEVICE_SERIAL)

    error = adbDevice.check_device_connection()

    self.assertEqual(error, None)

  @mock.patch.object(subprocess, "run", autospec=True)
  def test_check_device_connection_serial_arg_not_in_devices_error(self,
      mock_subprocess_run):
    mock_subprocess_run.return_value = (
        self.generate_adb_devices_result([MOCK_DEVICE_SERIAL]))
    invalid_device_serial = "invalid-device-serial"
    adbDevice = AdbDevice(invalid_device_serial)

    error = adbDevice.check_device_connection()

    self.assertNotEqual(error, None)
    self.assertEqual(error.message, ("Device with serial %s is not connected."
                                     % invalid_device_serial))
    self.assertEqual(error.suggestion, None)

  @mock.patch.dict(os.environ, {"ANDROID_SERIAL": MOCK_DEVICE_SERIAL},
                   clear=True)
  @mock.patch.object(subprocess, "run", autospec=True)
  def test_check_device_connection_env_variable_in_devices(self,
      mock_subprocess_run):
    mock_subprocess_run.return_value = (
        self.generate_adb_devices_result([MOCK_DEVICE_SERIAL]))
    adbDevice = AdbDevice(None)

    error = adbDevice.check_device_connection()

    self.assertEqual(error, None)
    self.assertEqual(adbDevice.serial, MOCK_DEVICE_SERIAL)

  @mock.patch.dict(os.environ, {"ANDROID_SERIAL": "invalid-device-serial"},
                   clear=True)
  @mock.patch.object(subprocess, "run", autospec=True)
  def test_check_device_connection_env_variable_not_in_devices_error(self,
      mock_subprocess_run):
    mock_subprocess_run.return_value = (
        self.generate_adb_devices_result([MOCK_DEVICE_SERIAL]))
    adbDevice = AdbDevice(None)

    error = adbDevice.check_device_connection()

    self.assertNotEqual(error, None)
    self.assertEqual(error.message, ("Device with serial invalid-device-serial"
                                     " is set as environment variable,"
                                     " ANDROID_SERIAL, but is not connected."))
    self.assertEqual(error.suggestion, None)

  @mock.patch.object(subprocess, "run", autospec=True)
  def test_check_device_connection_adb_devices_command_fails_error(self,
      mock_subprocess_run):
    mock_subprocess_run.side_effect = Exception(MOCK_FAILURE)
    adbDevice = AdbDevice(None)

    error = adbDevice.check_device_connection()

    self.assertNotEqual(error, None)
    self.assertEqual(error.message, ("Command 'adb devices' failed. %s"
                                     % MOCK_FAILURE))
    self.assertEqual(error.suggestion, None)

  @mock.patch.object(subprocess, "run", autospec=True)
  def test_check_device_connection_no_devices_connected_error(self,
      mock_subprocess_run):
    mock_subprocess_run.return_value = (self.generate_adb_devices_result([]))
    adbDevice = AdbDevice(None)

    error = adbDevice.check_device_connection()

    self.assertNotEqual(error, None)
    self.assertEqual(error.message, "There are currently no devices connected.")
    self.assertEqual(error.suggestion, None)

  @mock.patch.object(subprocess, "run", autospec=True)
  def test_check_device_connection_no_devices_connected_adb_not_started_error(
      self, mock_subprocess_run):
    mock_subprocess_run.return_value = (
        self.generate_adb_devices_result([], False))
    adbDevice = AdbDevice(None)

    error = adbDevice.check_device_connection()

    self.assertNotEqual(error, None)
    self.assertEqual(error.message, "There are currently no devices connected.")
    self.assertEqual(error.suggestion, None)

  @mock.patch.dict(os.environ, {}, clear=True)
  @mock.patch.object(subprocess, "run", autospec=True)
  def test_check_device_connection_only_one_device(self, mock_subprocess_run):
    mock_subprocess_run.return_value = (
        self.generate_adb_devices_result([MOCK_DEVICE_SERIAL]))
    adbDevice = AdbDevice(None)

    error = adbDevice.check_device_connection()

    self.assertEqual(error, None)
    self.assertEqual(adbDevice.serial, MOCK_DEVICE_SERIAL)

  @mock.patch.dict(os.environ, {}, clear=True)
  @mock.patch.object(subprocess, "run", autospec=True)
  def test_check_device_connection_multiple_devices_error(self,
      mock_subprocess_run):
    mock_subprocess_run.return_value = (
        self.generate_adb_devices_result([MOCK_DEVICE_SERIAL,
                                          MOCK_DEVICE_SERIAL2]))
    adbDevice = AdbDevice(None)

    error = adbDevice.check_device_connection()

    self.assertNotEqual(error, None)
    self.assertEqual(error.message, ("There is more than one device currently"
                                     " connected."))
    self.assertEqual(error.suggestion, ("Run one of the following commands to"
                                        " choose one of the connected devices:"
                                        "\n\t torq --serial %s"
                                        "\n\t torq --serial %s"
                                        % (MOCK_DEVICE_SERIAL,
                                           MOCK_DEVICE_SERIAL2)))


if __name__ == '__main__':
  unittest.main()
