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
import subprocess
from unittest import mock
from command import ProfilerCommand
from device import AdbDevice
from torq import DEFAULT_DUR_MS, DEFAULT_OUT_DIR

PROFILER_COMMAND_TYPE = "profiler"
TEST_ERROR_MSG = "test-error"
TEST_EXCEPTION = Exception(TEST_ERROR_MSG)
TEST_SERIAL = "test-serial"
DEFAULT_PERFETTO_CONFIG = "default"
TEST_USER_ID_1 = 0
TEST_USER_ID_2 = 1
TEST_USER_ID_3 = 2


class ProfilerCommandExecutorUnitTest(unittest.TestCase):

  def setUp(self):
    self.command = ProfilerCommand(
        PROFILER_COMMAND_TYPE, "custom", None, DEFAULT_OUT_DIR, DEFAULT_DUR_MS,
        None, 1, None, DEFAULT_PERFETTO_CONFIG, None, False, [], [], None, None)
    self.mock_device = mock.create_autospec(AdbDevice, instance=True,
                                            serial=TEST_SERIAL)
    self.mock_device.check_device_connection.return_value = None

  @mock.patch.object(subprocess, "Popen", autospec=True)
  def test_execute_one_run_and_use_ui_success(self, mock_process):
    with mock.patch("command_executor.open_trace", autospec=True):
      self.command.use_ui = True
      self.mock_device.start_perfetto_trace.return_value = mock_process

      error = self.command.execute(self.mock_device)

      self.assertEqual(error, None)
      self.assertEqual(self.mock_device.pull_file.call_count, 1)

  @mock.patch.object(subprocess, "Popen", autospec=True)
  def test_execute_one_run_no_ui_success(self, mock_process):
    self.mock_device.start_perfetto_trace.return_value = mock_process

    error = self.command.execute(self.mock_device)

    self.assertEqual(error, None)
    self.assertEqual(self.mock_device.pull_file.call_count, 1)

  def test_execute_check_device_connection_failure(self):
    self.mock_device.check_device_connection.side_effect = TEST_EXCEPTION

    with self.assertRaises(Exception) as e:
      self.command.execute(self.mock_device)

    self.assertEqual(str(e.exception), TEST_ERROR_MSG)
    self.assertEqual(self.mock_device.pull_file.call_count, 0)

  def test_execute_create_default_config_no_dur_ms_error(self):
    self.command.dur_ms = None

    with self.assertRaises(ValueError) as e:
      self.command.execute(self.mock_device)

    self.assertEqual(str(e.exception),
                     "Cannot create config because a valid dur_ms was not set.")
    self.assertEqual(self.mock_device.pull_file.call_count, 0)

  def test_execute_create_default_config_bad_excluded_ftrace_event_error(self):
    self.command.excluded_ftrace_events = ["mock-ftrace-event"]

    error = self.command.execute(self.mock_device)

    self.assertNotEqual(error, None)
    self.assertEqual(error.message,
                     ("Cannot remove ftrace event %s from config because it is"
                      " not one of the config's ftrace events."
                      % self.command.excluded_ftrace_events[0]))
    self.assertEqual(error.suggestion, ("Please specify one of the following"
                                        " possible ftrace events:\n\t"
                                        " dmabuf_heap/dma_heap_stat\n\t"
                                        " ftrace/print\n\t"
                                        " gpu_mem/gpu_mem_total\n\t"
                                        " ion/ion_stat\n\t"
                                        " kmem/ion_heap_grow\n\t"
                                        " kmem/ion_heap_shrink\n\t"
                                        " kmem/rss_stat\n\t"
                                        " lowmemorykiller/lowmemory_kill\n\t"
                                        " mm_event/mm_event_record\n\t"
                                        " oom/mark_victim\n\t"
                                        " oom/oom_score_adj_update\n\t"
                                        " power/cpu_frequency\n\t"
                                        " power/cpu_idle\n\t"
                                        " power/gpu_frequency\n\t"
                                        " power/suspend_resume\n\t"
                                        " power/wakeup_source_activate\n\t"
                                        " power/wakeup_source_deactivate\n\t"
                                        " sched/sched_blocked_reason\n\t"
                                        " sched/sched_process_exit\n\t"
                                        " sched/sched_process_free\n\t"
                                        " sched/sched_switch\n\t"
                                        " sched/sched_wakeup\n\t"
                                        " sched/sched_wakeup_new\n\t"
                                        " sched/sched_waking\n\t"
                                        " task/task_newtask\n\t"
                                        " task/task_rename\n\t"
                                        " vmscan/*\n\t"
                                        " workqueue/*"))
    self.assertEqual(self.mock_device.pull_file.call_count, 0)

  def test_execute_create_default_config_bad_included_ftrace_event_error(self):
    self.command.included_ftrace_events = ["power/cpu_idle"]

    error = self.command.execute(self.mock_device)

    self.assertNotEqual(error, None)
    self.assertEqual(error.message,
                     ("Cannot add ftrace event %s to config because it is"
                      " already one of the config's ftrace events."
                      % self.command.included_ftrace_events[0]))
    self.assertEqual(error.suggestion, ("Please do not specify any of the"
                                        " following ftrace events that are"
                                        " already included:\n\t"
                                        " dmabuf_heap/dma_heap_stat\n\t"
                                        " ftrace/print\n\t"
                                        " gpu_mem/gpu_mem_total\n\t"
                                        " ion/ion_stat\n\t"
                                        " kmem/ion_heap_grow\n\t"
                                        " kmem/ion_heap_shrink\n\t"
                                        " kmem/rss_stat\n\t"
                                        " lowmemorykiller/lowmemory_kill\n\t"
                                        " mm_event/mm_event_record\n\t"
                                        " oom/mark_victim\n\t"
                                        " oom/oom_score_adj_update\n\t"
                                        " power/cpu_frequency\n\t"
                                        " power/cpu_idle\n\t"
                                        " power/gpu_frequency\n\t"
                                        " power/suspend_resume\n\t"
                                        " power/wakeup_source_activate\n\t"
                                        " power/wakeup_source_deactivate\n\t"
                                        " sched/sched_blocked_reason\n\t"
                                        " sched/sched_process_exit\n\t"
                                        " sched/sched_process_free\n\t"
                                        " sched/sched_switch\n\t"
                                        " sched/sched_wakeup\n\t"
                                        " sched/sched_wakeup_new\n\t"
                                        " sched/sched_waking\n\t"
                                        " task/task_newtask\n\t"
                                        " task/task_rename\n\t"
                                        " vmscan/*\n\t"
                                        " workqueue/*"))
    self.assertEqual(self.mock_device.pull_file.call_count, 0)

  def test_execute_run_root_failure(self):
    self.mock_device.root_device.side_effect = TEST_EXCEPTION

    with self.assertRaises(Exception) as e:
      self.command.execute(self.mock_device)

    self.assertEqual(str(e.exception), TEST_ERROR_MSG)
    self.assertEqual(self.mock_device.pull_file.call_count, 0)

  def test_execute_remove_file_failure(self):
    self.mock_device.remove_file.side_effect = TEST_EXCEPTION

    with self.assertRaises(Exception) as e:
      self.command.execute(self.mock_device)

    self.assertEqual(str(e.exception), TEST_ERROR_MSG)
    self.assertEqual(self.mock_device.pull_file.call_count, 0)

  def test_execute_start_perfetto_trace_failure(self):
    self.mock_device.start_perfetto_trace.side_effect = TEST_EXCEPTION

    with self.assertRaises(Exception) as e:
      self.command.execute(self.mock_device)

    self.assertEqual(str(e.exception), TEST_ERROR_MSG)
    self.assertEqual(self.mock_device.pull_file.call_count, 0)

  @mock.patch.object(subprocess, "Popen", autospec=True)
  def test_execute_process_wait_failure(self, mock_process):
    self.mock_device.start_perfetto_trace.return_value = mock_process
    mock_process.wait.side_effect = TEST_EXCEPTION

    with self.assertRaises(Exception) as e:
      self.command.execute(self.mock_device)

    self.assertEqual(str(e.exception), TEST_ERROR_MSG)
    self.assertEqual(self.mock_device.pull_file.call_count, 0)

  @mock.patch.object(subprocess, "Popen", autospec=True)
  def test_execute_pull_file_failure(self, mock_process):
    self.mock_device.start_perfetto_trace.return_value = mock_process
    self.mock_device.pull_file.side_effect = TEST_EXCEPTION

    with self.assertRaises(Exception) as e:
      self.command.execute(self.mock_device)

    self.assertEqual(str(e.exception), TEST_ERROR_MSG)
    self.assertEqual(self.mock_device.pull_file.call_count, 1)


class UserSwitchCommandExecutorUnitTest(unittest.TestCase):

  def simulate_user_switch(self, user):
    self.current_user = user

  def setUp(self):
    self.command = ProfilerCommand(
        PROFILER_COMMAND_TYPE, "user-switch", None, DEFAULT_OUT_DIR,
        DEFAULT_DUR_MS, None, 1, None, DEFAULT_PERFETTO_CONFIG, None, False, [],
        [], None, None)
    self.mock_device = mock.create_autospec(AdbDevice, instance=True,
                                            serial=TEST_SERIAL)
    self.mock_device.check_device_connection.return_value = None
    self.mock_device.user_exists.return_value = None
    self.current_user = TEST_USER_ID_3
    self.mock_device.get_current_user.side_effect = lambda: self.current_user

  @mock.patch.object(subprocess, "Popen", autospec=True)
  def test_execute_all_users_different_success(self, mock_process):
    self.command.from_user = TEST_USER_ID_1
    self.command.to_user = TEST_USER_ID_2
    self.mock_device.start_perfetto_trace.return_value = mock_process
    self.mock_device.perform_user_switch.side_effect = (
        lambda user: self.simulate_user_switch(user))

    error = self.command.execute(self.mock_device)

    self.assertEqual(error, None)
    self.assertEqual(self.current_user, TEST_USER_ID_3)
    self.assertEqual(self.mock_device.perform_user_switch.call_count, 3)
    self.assertEqual(self.mock_device.pull_file.call_count, 1)

  @mock.patch.object(subprocess, "Popen", autospec=True)
  def test_execute_perform_user_switch_failure(self, mock_process):
    self.command.from_user = TEST_USER_ID_2
    self.command.to_user = TEST_USER_ID_1
    self.mock_device.start_perfetto_trace.return_value = mock_process
    self.mock_device.perform_user_switch.side_effect = TEST_EXCEPTION

    with self.assertRaises(Exception) as e:
      self.command.execute(self.mock_device)

    self.assertEqual(str(e.exception), TEST_ERROR_MSG)
    self.assertEqual(self.mock_device.perform_user_switch.call_count, 1)
    self.assertEqual(self.mock_device.pull_file.call_count, 0)

  def test_execute_to_user_is_from_user_error(self):
    self.command.from_user = TEST_USER_ID_1
    self.command.to_user = TEST_USER_ID_1

    error = self.command.execute(self.mock_device)

    self.assertNotEqual(error, None)
    self.assertEqual(error.message, ("Cannot perform user-switch to user %s"
                                     " because the current user on device"
                                     " %s is already %s."
                                     % (TEST_USER_ID_1, TEST_SERIAL,
                                        TEST_USER_ID_1)))
    self.assertEqual(error.suggestion, ("Choose a --to-user ID that is"
                                        " different than the --from-user ID."))
    self.assertEqual(self.mock_device.perform_user_switch.call_count, 0)
    self.assertEqual(self.mock_device.pull_file.call_count, 0)

  @mock.patch.object(subprocess, "Popen", autospec=True)
  def test_execute_from_user_empty_success(self, mock_process):
    self.command.from_user = None
    self.command.to_user = TEST_USER_ID_2
    self.mock_device.start_perfetto_trace.return_value = mock_process
    self.mock_device.perform_user_switch.side_effect = (
        lambda user: self.simulate_user_switch(user))

    error = self.command.execute(self.mock_device)

    self.assertEqual(error, None)
    self.assertEqual(self.current_user, TEST_USER_ID_3)
    self.assertEqual(self.mock_device.perform_user_switch.call_count, 2)
    self.assertEqual(self.mock_device.pull_file.call_count, 1)

  def test_execute_to_user_is_current_user_and_from_user_empty_error(self):
    self.command.from_user = None
    self.command.to_user = self.current_user

    error = self.command.execute(self.mock_device)

    self.assertNotEqual(error, None)
    self.assertEqual(error.message, ("Cannot perform user-switch to user %s"
                                     " because the current user on device"
                                     " %s is already %s."
                                     % (self.current_user, TEST_SERIAL,
                                        self.current_user)))
    self.assertEqual(error.suggestion, ("Choose a --to-user ID that is"
                                        " different than the --from-user ID."))
    self.assertEqual(self.mock_device.perform_user_switch.call_count, 0)
    self.assertEqual(self.mock_device.pull_file.call_count, 0)

  @mock.patch.object(subprocess, "Popen", autospec=True)
  def test_execute_from_user_is_current_user_success(self, mock_process):
    self.command.from_user = self.current_user
    self.command.to_user = TEST_USER_ID_2
    self.mock_device.start_perfetto_trace.return_value = mock_process
    self.mock_device.perform_user_switch.side_effect = (
        lambda user: self.simulate_user_switch(user))

    error = self.command.execute(self.mock_device)

    self.assertEqual(error, None)
    self.assertEqual(self.current_user, TEST_USER_ID_3)
    self.assertEqual(self.mock_device.perform_user_switch.call_count, 2)
    self.assertEqual(self.mock_device.pull_file.call_count, 1)

  @mock.patch.object(subprocess, "Popen", autospec=True)
  def test_execute_to_user_is_current_user_success(self, mock_process):
    self.command.from_user = TEST_USER_ID_1
    self.command.to_user = self.current_user
    self.mock_device.start_perfetto_trace.return_value = mock_process
    self.mock_device.perform_user_switch.side_effect = (
        lambda user: self.simulate_user_switch(user))

    error = self.command.execute(self.mock_device)

    self.assertEqual(error, None)
    self.assertEqual(self.current_user, TEST_USER_ID_3)
    self.assertEqual(self.mock_device.perform_user_switch.call_count, 2)
    self.assertEqual(self.mock_device.pull_file.call_count, 1)


if __name__ == '__main__':
  unittest.main()
