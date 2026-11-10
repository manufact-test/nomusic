package pro.celikom.ownedplayer;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.ScrollView;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Independent CELIKOM first-party catalogue player. NO Yandex UI/credentials.
 * Product does NOT claim to contain the Yandex licensed original catalogue.
 */
public final class MainActivity extends Activity {
    private static final int BG=Color.rgb(11,16,19);
    private static final int SURFACE=Color.rgb(20,27,31);
    private static final int INK=Color.rgb(244,247,248);
    private static final int CYAN=Color.rgb(102,224,255);
    private final ExecutorService background=Executors.newSingleThreadExecutor();
    private final Handler main=new Handler(Looper.getMainLooper());
    private OwnedApiClient api;
    private OwnedCatalogue catalogue;
    private OwnedCatalogue.Track selected;
    private EditText email,password,code,search;
    private TextView status,selection;
    private ArrayAdapter<String> listAdapter;
    private final List<OwnedCatalogue.Track> visible=new ArrayList<>();
    private String pendingEmail;

    @Override public void onCreate(Bundle savedInstanceState){
        super.onCreate(savedInstanceState);
        api=OwnedApiClient.get(this);
        LinearLayout layout=new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setBackgroundColor(BG);layout.setPadding(24,18,24,16);

        TextView header=text("CELIKOM",25,CYAN);
        layout.addView(header);
        layout.addView(text("Своя музыка. Один плеер. Только доступные версии CELIKOM.",13,INK));
        layout.addView(text("Полный каталог Яндекс.Музыки сюда не входит.",12,INK));

        email=field("Почта CELIKOM",false);
        password=field("Пароль CELIKOM",true);
        code=field("Код подтверждения почты",false);
        layout.addView(email);layout.addView(password);layout.addView(code);

        row(layout,
                button("Войти",()->perform(()->{
                    pendingEmail=email.getText().toString().trim();
                    boolean verification=api.login(pendingEmail,password.getText().toString())
                            .optBoolean("verification_required",false);
                    return verification?"Проверьте почту и введите код":"Вход выполнен";
                })),
                button("Подтвердить код",()->perform(()->{
                    api.verify(pendingEmail!=null?pendingEmail:email.getText().toString(),
                            code.getText().toString());
                    return "Почта подтверждена";
                })));
        row(layout,
                button("Проверить доступ",()->perform(()->api.entitled()
                    ?"Подписка CELIKOM активна":"Нет действующего доступа")),
                button("Активировать пробный период",()->perform(()->api.activate()
                    ?"Доступ активирован сервером":"Сервер отказал в активации")));
        row(layout,
                button("Загрузить каталог",()->perform(()->{
                    OwnedCatalogue approved=api.catalogue();
                    main.post(()->{catalogue=approved;redraw("");});
                    return "Одобрено версий: "+approved.count();
                })),
                button("Выйти",()->{
                    send(OwnedPlaybackService.STOP,null);
                    perform(()->{api.logout();main.post(()->{
                        catalogue=null;selected=null;visible.clear();
                        listAdapter.clear();selection.setText("Трек не выбран");
                    });return "Вы вышли";});
                }));

        search=field("Поиск по доступным версиям",false);
        layout.addView(search);
        search.addTextChangedListener(new TextWatcher(){
            @Override public void beforeTextChanged(CharSequence s,int start,int count,int after){}
            @Override public void onTextChanged(CharSequence s,int start,int before,int count){
                redraw(s.toString());
            }
            @Override public void afterTextChanged(Editable s){}
        });
        listAdapter=new ArrayAdapter<>(this,android.R.layout.simple_list_item_1,
                new ArrayList<>());
        ListView list=new ListView(this);
        list.setBackgroundColor(SURFACE);
        list.setAdapter(listAdapter);
        layout.addView(list,new LinearLayout.LayoutParams(-1,0,1f));
        list.setOnItemClickListener((parent,view,position,id)->{
            if(position<0||position>=visible.size())return;
            selected=visible.get(position);
            selection.setText("Выбрано: "+selected.title+" — "+selected.artist);
        });

        selection=text("Трек не выбран",13,INK);
        layout.addView(selection);
        row(layout,
            button("Играть",()->{
                if(selected==null){status.setText("Сначала выберите трек");return;}
                send(OwnedPlaybackService.PLAY,selected.id);
                status.setText("Проверяем права и готовим трек…");
            }),
            button("Пауза / Продолжить",()->send(OwnedPlaybackService.TOGGLE,null)));
        row(layout,
            button("−15 сек",()->send(OwnedPlaybackService.SEEK_BACK,null)),
            button("+15 сек",()->send(OwnedPlaybackService.SEEK_FORWARD,null)));
        row(layout,
            button("Следующий",()->send(OwnedPlaybackService.NEXT,null)),
            button("Стоп",()->send(OwnedPlaybackService.STOP,null)));

        status=text("Войдите в CELIKOM",13,INK);
        layout.addView(status);
        setContentView(layout);
        main.postDelayed(refreshStatus,1500);
    }

    private TextView text(String value,int sp,int color){
        TextView v=new TextView(this);
        v.setText(value);v.setTextSize(sp);v.setTextColor(color);
        v.setPadding(8,8,8,8);
        return v;
    }
    private EditText field(String hint,boolean secret){
        EditText f=new EditText(this);
        f.setTextColor(INK);f.setHintTextColor(Color.LTGRAY);
        f.setHint(hint);f.setSingleLine(true);
        if(secret)f.setInputType(0x00000081);
        return f;
    }
    private Button button(String title,Runnable run){
        Button b=new Button(this);
        b.setText(title);b.setTextColor(CYAN);b.setAllCaps(false);
        b.setOnClickListener(v->run.run());
        return b;
    }
    private void row(LinearLayout root,Button first,Button second){
        LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);
        row.addView(first,new LinearLayout.LayoutParams(0,-2,1));
        row.addView(second,new LinearLayout.LayoutParams(0,-2,1));
        root.addView(row);
    }
    private interface Work { String apply()throws Exception; }
    private void perform(Work job){
        status.setText("Обращаемся к CELIKOM…");
        background.execute(()->{
            String value;
            try{value=job.apply();}catch(Exception ex){value="Проверка не выполнена. Доступ не выдан.";}
            final String message=value;
            main.post(()->status.setText(message));
        });
    }
    private void redraw(String query){
        if(listAdapter==null)return;
        visible.clear();listAdapter.clear();
        if(catalogue!=null){
            visible.addAll(catalogue.search(query,150));
            for(OwnedCatalogue.Track track:visible)
                listAdapter.add(track.title+" — "+track.artist);
        }
        listAdapter.notifyDataSetChanged();
    }
    private void send(String action,String id){
        Intent intent=new Intent(this,OwnedPlaybackService.class);
        intent.setAction(action);
        if(id!=null)intent.putExtra(OwnedPlaybackService.EXTRA_TRACK,id);
        startService(intent);
    }
    private final Runnable refreshStatus=new Runnable(){
        @Override public void run(){
            String message=getSharedPreferences("owned-playback",MODE_PRIVATE)
                    .getString("state",null);
            if(message!=null&&status!=null&&!status.getText().toString().startsWith("Обращаемся"))
                status.setText(message);
            main.postDelayed(this,1500);
        }
    };
    @Override protected void onDestroy(){
        main.removeCallbacks(refreshStatus);
        background.shutdownNow();
        super.onDestroy();
    }
}
