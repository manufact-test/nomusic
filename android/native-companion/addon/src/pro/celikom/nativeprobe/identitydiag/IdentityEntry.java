package pro.celikom.nativeprobe.identitydiag;
import android.app.Activity;
import android.content.Intent;
import android.view.*;
import android.widget.*;
/** Add one entry to the existing CELIKOM activity without replacing its features. */
public final class IdentityEntry {
 public static void attach(Activity a){try{LogStore.init(a);if(!a.getIntent().getBooleanExtra("legacy_tools",false)){Intent next=new Intent(a,RecorderActivity.class).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);if(Intent.ACTION_SEND.equals(a.getIntent().getAction()))next.setAction(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT,a.getIntent().getCharSequenceExtra(Intent.EXTRA_TEXT));a.startActivity(next);a.finish();return;}View root=a.findViewById(android.R.id.content);LinearLayout target=find(root);if(target!=null&&target.findViewWithTag("celikom_identity_entry")==null){Button b=new Button(a);b.setTag("celikom_identity_entry");b.setText("Комплексная проверка и замена");b.setAllCaps(false);b.setOnClickListener(v->a.startActivity(new Intent(a,RecorderActivity.class)));target.addView(b,Math.min(1,target.getChildCount()),new LinearLayout.LayoutParams(-1,-2));}forward(a,a.getIntent());}catch(Throwable ignored){}}
 private static LinearLayout find(View v){if(v instanceof LinearLayout&&((LinearLayout)v).getOrientation()==LinearLayout.VERTICAL)return (LinearLayout)v;if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++){LinearLayout found=find(g.getChildAt(i));if(found!=null)return found;}}return null;}
 public static void forward(Activity a,Intent i){try{if(!LogStore.active||i==null||!Intent.ACTION_SEND.equals(i.getAction()))return;CharSequence text=i.getCharSequenceExtra(Intent.EXTRA_TEXT);if(text==null||ShareLinks.parse(text.toString()).isEmpty())return;a.startActivity(new Intent(a,RecorderActivity.class).setAction(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT,text.toString()).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP));}catch(Throwable ignored){}}
}
