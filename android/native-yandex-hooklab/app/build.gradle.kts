plugins {
    id("com.android.application")
}
android {
    namespace = "pro.celikom.yandex.nativehooklab"
    compileSdk = 35
    defaultConfig {
        applicationId = "pro.celikom.yandex.nativehooklab"
        minSdk = 28
        targetSdk = 33
        versionCode = 1
        versionName = "0.0.1-readonly-lab"
    }
    buildTypes {
        getByName("debug") {
            isMinifyEnabled = false
            buildConfigField("boolean", "ALLOW_SOURCE_MUTATION", "false")
        }
        getByName("release") {
            isMinifyEnabled = false
            buildConfigField("boolean", "ALLOW_SOURCE_MUTATION", "false")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    buildFeatures {
        buildConfig = true
    }
    packaging {
        resources {
            merges += "META-INF/xposed/*"
        }
    }
}
dependencies {
    compileOnly("io.github.libxposed:api:102.0.0")
}
