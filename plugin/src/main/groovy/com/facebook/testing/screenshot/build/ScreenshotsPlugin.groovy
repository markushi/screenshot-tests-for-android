package com.facebook.testing.screenshot.build

import org.gradle.api.*
import java.io.File;

class ScreenshotsPluginExtension {
    def testApkTarget = "packageDebugAndroidTest"
    def connectedAndroidTestTarget = "connectedAndroidTest"
    def customTestRunner = false
    def recordDir = null
    def verifyDir = null
    def addCompileDeps = true
    def screenshotTestPackage = null
}

class ScreenshotsPlugin implements Plugin<Project> {

  void apply(Project project) {
    project.extensions.create("screenshots", ScreenshotsPluginExtension)

    // We'll figure out the adb in afterEvaluate
    def adb = null

    if (project.screenshots.addCompileDeps) {
      addRuntimeDep(project)
    }

    project.task('recordScreenshots') {
      doLast {
        recordScreenshots(project, false)
      }
    }

    project.task('verifyScreenshots') {
      doLast {
        recordScreenshots(project, true)
      }
    }

    project.task("clearScreenshots") {
      doLast {
        project.exec {
          executable = adb
          args = ["shell", "rm", "-rf", "\$EXTERNAL_STORAGE/screenshots"]
          ignoreExitValue = true
        }
      }
    }

    project.afterEvaluate {
      if (project.screenshots.screenshotTestPackage != null) {
        project.android.defaultConfig.testInstrumentationRunnerArguments.put("package", project.screenshots.screenshotTestPackage)
      }

      adb = project.android.getAdbExe().toString()
      project.task("recordScreenshotTests")
      project.recordScreenshotTests.group "screenshotTests"
      project.recordScreenshotTests.dependsOn project.clearScreenshots
      project.recordScreenshotTests.dependsOn project.screenshots.connectedAndroidTestTarget
      project.recordScreenshotTests.dependsOn project.recordScreenshots

      project.task("verifyScreenshotTests")
      project.verifyScreenshotTests.group "screenshotTests"
      project.verifyScreenshotTests.dependsOn project.clearScreenshots
      project.verifyScreenshotTests.dependsOn project.screenshots.connectedAndroidTestTarget
      project.verifyScreenshotTests.dependsOn project.verifyScreenshots

      project.recordScreenshots.dependsOn project.screenshots.testApkTarget
      project.verifyScreenshots.dependsOn project.screenshots.testApkTarget
    }

    if (!project.screenshots.customTestRunner) {
      project.android.defaultConfig {
        testInstrumentationRunner = 'com.facebook.testing.screenshot.ScreenshotTestRunner'
      }
    }
  }

  File getVerifyDir(Project project) {
    if (project.screenshots.verifyDir != null) {
      return new File(project.getProjectDir(), project.screenshots.verifyDir)
    } else {
      return new File(project.getProjectDir(), "screenshots")
    }
  }

  File getRecordDir(Project project) {
    if (project.screenshots.recordDir != null) {
      return new File(project.getProjectDir(), project.screenshots.recordDir)
    } else {
      return new File(project.getBuildDir(), "reports" + File.separator + "screenshots")
    }
  }

  void recordScreenshots(Project project, boolean verify) {
    project.exec {
        def apkFile = getTestApkOutput(project)

        def codeSource = ScreenshotsPlugin.class.getProtectionDomain().getCodeSource()
        def jarFile = new File(codeSource.getLocation().toURI().getPath())
        executable = 'python'
        environment('PYTHONPATH', jarFile)

        args = ['-m', 'android_screenshot_tests.main', "--apk"]
        if (verify) {
          args += ["--verify"]
        } else {
          args += ["--record"]
        }
        args += ["--record-dir=" + getRecordDir(project).getAbsolutePath()]
        args += ["--verify-dir=" + getVerifyDir(project).getAbsolutePath()]
        args += [apkFile.toString()]
      }
  }

  String getTestApkOutput(Project project) {

    return project.tasks.getByPath(project.screenshots.testApkTarget).getOutputs().getFiles().filter {
      it.getAbsolutePath().endsWith ".apk"
    }.getSingleFile().getAbsolutePath()
  }

  void addRuntimeDep(Project project) {
    def implementationVersion = getClass().getPackage().getImplementationVersion()

    if (!implementationVersion) {
      println("WARNING: you shouldn't see this in normal operation, file a bug report if this is not a framework test")
      implementationVersion = '0.4.2'
    }

    project.dependencies.androidTestCompile('com.facebook.testing.screenshot:core:' + implementationVersion)
  }
}
