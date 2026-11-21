#!/usr/bin/env python3
"""JVM regression tests for the exact publisher Retrofit proxy contract."""
import pathlib
import subprocess
import tempfile
import unittest

BASE = pathlib.Path(__file__).resolve().parents[1]
MODULE = BASE / "exit-callsite-witness-module/app/src/main/java/pro/celikom/a1exitwitness"
TESTS = BASE / "tests/src"
HOOK = MODULE / "ExitCallsiteWitness.java"


class IssuerProxyContractTest(unittest.TestCase):
    def test_real_java_proxy_shapes_on_jvm(self):
        sources = [
            MODULE / "PublisherTrackIdProxyContract.java",
            TESTS / "retrofit2/http/Query.java",
            TESTS / "retrofit2/http/Path.java",
            TESTS / "Vz8.java",
            TESTS / "fj7.java",
            TESTS / "ObfuscatedPublisherApis.java",
            TESTS / "pro/celikom/a1exitwitness/PublisherTrackIdProxyContractTest.java",
        ]
        with tempfile.TemporaryDirectory(prefix="celikom-issuer-proxy-jvm-") as tmp:
            subprocess.run(
                ["javac", "--release", "17", "-d", tmp, *map(str, sources)],
                check=True, text=True,
            )
            result = subprocess.run(
                ["java", "-cp", tmp,
                 "pro.celikom.a1exitwitness.PublisherTrackIdProxyContractTest"],
                check=True, capture_output=True, text=True,
            )
            self.assertIn(
                "ISSUER_PROXY_INHERITED_DECLARED_ANNOTATION_CLASSLOADER_PASS",
                result.stdout,
            )

    def test_runtime_hook_uses_exact_proxy_shape_and_original_handler_once(self):
        code = HOOK.read_text(encoding="utf-8")
        start = code.index("private synchronized void hookConcretePublisherTrackIdProxy(")
        end = code.index("private synchronized void installPublisherTrackIdProxyWitness(", start)
        selection = code[start:end]
        self.assertIn("PublisherTrackIdProxyContract.inspect(", selection)
        self.assertIn("inspection.proxyInterfacesMatchRequested", selection)
        self.assertIn("inspection.apiImplemented", selection)
        self.assertNotIn("issuerApi.getDeclaredMethods()", selection)

        intercept_start = selection.index("hook(concrete).setExceptionMode")
        intercept = selection[intercept_start:]
        self.assertEqual(intercept.count("chain.proceed()"), 1)
        self.assertIn(
            "return chain.proceed(); // original Retrofit handler ONCE",
            intercept,
        )
        self.assertNotIn("handler.invoke(", intercept)
        policy = (MODULE / "NativeTrackIdBetaPolicy.java").read_text(encoding="utf-8")
        self.assertIn("recordProxyShape(", policy)
        self.assertIn("proxyShapeSummary()", policy)
        self.assertIn("NativeTrackIdBetaPolicy.proxyShapeSummary()", code)


if __name__ == "__main__":
    unittest.main()
