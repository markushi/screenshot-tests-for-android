/**
 * Copyright (c) 2014-present, Facebook, Inc.
 * All rights reserved.
 *
 * This source code is licensed under the BSD-style license found in the
 * LICENSE file in the root directory of this source tree. An additional grant
 * of patent rights can be found in the PATENTS file in the same directory.
 */

package com.facebook.testing.screenshot.internal;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Environment;
import android.app.Instrumentation;
import android.content.Context;
import android.support.test.uiautomator.UiDevice;

import java.io.File;
import java.io.IOException;

/**
 * Provides a directory for an Album to store its screenshots in.
 */
class ScreenshotDirectories {
  private Context mContext;

  public ScreenshotDirectories(Context context) {
    mContext = context;
  }

  public File get(String type) {
    checkPermissions();
    return getSdcardDir(type);
  }

  private void checkPermissions() {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
      final Instrumentation instrumentation = Registry.getRegistry().instrumentation;
      final UiDevice device = UiDevice.getInstance(instrumentation);
      final String packageName = instrumentation.getTargetContext().getPackageName();
      try {
        device.executeShellCommand("pm grant " + packageName + " " + Manifest.permission.READ_EXTERNAL_STORAGE);
        device.executeShellCommand("pm grant " + packageName + " " + Manifest.permission.WRITE_EXTERNAL_STORAGE);
      } catch (IOException e) {
        throw new RuntimeException("Could not grant storage permissions", e);
      }
    }
  }

  private File getSdcardDir(String type) {
    String externalStorage = System.getenv("EXTERNAL_STORAGE");

    if (externalStorage == null) {
      throw new RuntimeException("No $EXTERNAL_STORAGE has been set on the device, please report this bug!");
    }

    String parent = String.format(
      "%s/screenshots/%s/",
      externalStorage,
      mContext.getPackageName());

    String child = String.format("%s/screenshots-%s", parent, type);

    new File(parent).mkdirs();

    File dir = new File(child);
    dir.mkdir();

    if (!dir.exists()) {
      throw new RuntimeException("Failed to create the directory for screenshots. Is your sdcard directory read-only?");
    }

    setWorldWriteable(dir);
    return dir;
  }

  private File getDataDir(String type) {
    File dir = mContext.getDir("screenshots-" + type, Context.MODE_WORLD_READABLE);

    setWorldWriteable(dir);
    return dir;
  }

  private void setWorldWriteable(File dir) {
    // Context.MODE_WORLD_WRITEABLE has been deprecated, so let's
    // manually set this
    dir.setWritable(/* writeable = */ true, /* ownerOnly = */ false);
  }
}
