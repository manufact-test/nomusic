plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }
android {
    namespace = "pro.celikom.researchsource"
    compileSdk = 36
    defaultConfig { applicationId = "pro.celikom.researchsource"; minSdk = 28; targetSdk = 36 }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
}
