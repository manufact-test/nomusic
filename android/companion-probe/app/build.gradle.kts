plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }
android {
    namespace = "pro.celikom.nativeprobe"
    compileSdk = 36
    defaultConfig {
        applicationId = "pro.celikom.nativeprobe"; minSdk = 28; targetSdk = 36
        versionCode = 2; versionName = "0.3.1-probe"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
}
dependencies {
    implementation("androidx.core:core:1.13.1")
    androidTestImplementation("androidx.test.ext:junit:1.3.0")
    androidTestImplementation("androidx.test:runner:1.7.0")
}
