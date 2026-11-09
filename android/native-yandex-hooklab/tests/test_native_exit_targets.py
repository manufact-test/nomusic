import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_native_exit_calls_static import exit_target, TARGETS


class ExplicitExitTargetTest(unittest.TestCase):
    def test_only_exact_platform_termination_calls(self):
        for method, label in TARGETS.items():
            self.assertEqual(label, exit_target(method))

    def test_process_observation_and_activity_finish_not_misclassified(self):
        self.assertIsNone(exit_target(("Landroid/app/Activity;", "finish", "()V")))
        self.assertIsNone(exit_target(("Landroid/os/Process;", "myPid", "()I")))
        self.assertIsNone(exit_target(("Ljava/lang/System;", "gc", "()V")))
        self.assertIsNone(exit_target(("Lcom/yandex/SomeClass;", "exit", "(I)V")))


if __name__ == "__main__":
    unittest.main()
