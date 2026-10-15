'use strict';
// Laboratory instrumentation only. Never an ordinary-app identity proof.
Java.perform(function () {
  const Aiz = Java.use('aiz');
  const R63 = Java.use('r63');
  const List = Java.use('java.util.List');
  const Oju = Java.use('oju');
  const Track = Java.use('jbu');
  const meta = Aiz.s.overload('int');
  let currentId = null;
  let lastPair = null;
  function emit(event, data) { send(Object.assign({event:event, at_ms:Date.now(), lab_only:true}, data)); }
  function stack() {
    const frames=Java.use('java.lang.Thread').currentThread().getStackTrace();
    const rows=[];
    for(let i=2;i<frames.length && i<9;i++) rows.push(String(frames[i].getClassName())+'.'+String(frames[i].getMethodName()));
    return rows;
  }
  meta.implementation = function(index) {
    const result = meta.call(this,index);
    try {
      const state = Java.cast(this.c.value,R63);
      const selected = state.b.value;
      if (index !== selected) return result;
      const playable = Java.cast(state.f.value,List).get(index);
      if (String(playable.getClass().getName()) !== 'oju') return result;
      const song = Java.cast(playable,Oju);
      const id = String(Java.cast(song.a(),Track).a.value);
      const alias = String(song.b());
      if (!/^[1-9][0-9]{0,23}$/.test(id)) return result;
      currentId = id;
      const pair = id+'|'+alias;
      if (pair !== lastPair) {
        lastPair = pair;
        emit('current_metadata_identity',{catalogue_id:id, public_alias:alias, selected_index:selected});
      }
    } catch(e) { emit('metadata_hook_error',{error_type:String(e).slice(0,160)}); }
    return result;
  };
  const Parcel = Java.use('android.os.Parcel');
  const writeString = Parcel.writeString.overload('java.lang.String');
  let parcelEvents = 0;
  writeString.implementation = function(value) {
    try { if (currentId !== null && value !== null && String(value) === currentId && parcelEvents < 60) {
      parcelEvents++;
      emit('current_id_parceled',{catalogue_id:currentId,stack:stack()});
    } } catch(e) {}
    return writeString.call(this,value);
  };
  const Dar = Java.use('dar');
  const share = Dar.a.overload('p9r','java.lang.String','java.lang.String');
  share.implementation = function(item,invite,reference) {
    const result = share.call(this,item,invite,reference);
    try {
      const match = String(result).match(/\/track\/([1-9][0-9]*)/);
      if (match) emit('sharing_link_constructed',{catalogue_id:match[1], matches_selected:match[1]===currentId});
    } catch(e) {}
    return result;
  };
  emit('hooks_ready',{sources:['aiz.s/current-index','oju.a/jbu.a','oju.b','Parcel.writeString/exact-current-id','dar.a/track-id-only']});
});
