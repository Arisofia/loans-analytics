plugins {
    id("java")
    application
}

group = "com.abaco"
version = "0.0.1-SNAPSHOT"

repositories {
    mavenCentral()
}

// Enforce a compatible Java version for this project to ensure reproducible builds.
// This directly fixes the "Unsupported class file major version" error.
java {
    toolchain {
        languageVersion.set(JavaLanguageVersion.of(21))
    }
}

application {
    mainClass.set("com.abaco.Main")
}

dependencies {
    // Your project dependencies will be listed here.
}
