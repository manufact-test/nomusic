package pro.celikom.nativeprobe.identitydiag;
import android.app.Activity;
import android.content.Intent;
import android.view.*;
import android.widget.*;
/** Add one entry to the existing CELIKOM activity without replacing its features. */
public final class IdentityEntry {
 public static void attach(Activity a){try{LogStore.init(a);Intent next=new Intent(a,RecorderActivity.class).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);if(Intent.ACTION_SEND.equals(a.getIntent().getAction()))next.setAction(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT,a.getIntent().getCharSequenceExtra(Intent.EXTRA_TEXT));a.startActivity(next);a.finish();}catch(Throwable ignored){}}
 public static void forward(Activity a,Intent i){try{if(!LogStore.active||i==null||!Intent.ACTION_SEND.equals(i.getAction()))return;CharSequence text=i.getCharSequenceExtra(Intent.EXTRA_TEXT);if(text==null||ShareLinks.parse(text.toString()).isEmpty())return;a.startActivity(new Intent(a,RecorderActivity.class).setAction(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT,text.toString()).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP));}catch(Throwable ignored){}}
}
