package pro.celikom.spike
import android.content.ContentValues
import android.graphics.Bitmap
import android.os.Environment
import android.provider.MediaStore
import android.view.accessibility.AccessibilityNodeInfo
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class MobileUiTest {
    @Test fun accountControlsRemainAccessibleWithServiceRegionGate(){
        ActivityScenario.launch(MainActivity::class.java).use {
            val automation=InstrumentationRegistry.getInstrumentation().uiAutomation
            fun find(node:AccessibilityNodeInfo?,text:String):AccessibilityNodeInfo? {
                if(node==null)return null
                if(node.text?.toString()==text)return node
                for(i in 0 until node.childCount){find(node.getChild(i),text)?.let{return it}}
                return null
            }
            val until=System.currentTimeMillis()+5000
            var button:AccessibilityNodeInfo?=null
            while(System.currentTimeMillis()<until&&button==null){Thread.sleep(100);button=find(automation.rootInActiveWindow,"Аккаунт")}
            assertNotNull("Account menu must remain available",button)
            var target=button
            while(target!=null&&!target.isClickable)target=target.parent
            assertTrue(target?.performAction(AccessibilityNodeInfo.ACTION_CLICK)==true)
            Thread.sleep(800)
            assertNotNull(find(automation.rootInActiveWindow,"Войти"))
            assertNotNull(find(automation.rootInActiveWindow,"К плееру"))
            val bitmap=automation.takeScreenshot()?:error("Screenshot unavailable")
            val context=InstrumentationRegistry.getInstrumentation().targetContext
            val values=ContentValues().apply{put(MediaStore.MediaColumns.DISPLAY_NAME,"celikom-account.png");put(MediaStore.MediaColumns.MIME_TYPE,"image/png");put(MediaStore.MediaColumns.RELATIVE_PATH,Environment.DIRECTORY_DOWNLOADS)}
            val uri=context.contentResolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI,values)?:error("Cannot save screenshot")
            context.contentResolver.openOutputStream(uri)!!.use{assertTrue(bitmap.compress(Bitmap.CompressFormat.PNG,100,it))};bitmap.recycle()
        }
    }
}
