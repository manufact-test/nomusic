import pro.celikom.yandexweb.RangePolicy;
public final class TestRangePolicy {
  private static int count;
  private static void check(boolean v){if(!v)throw new AssertionError();count++;}
  private static void invalid(String s,long length){
    try{RangePolicy.parse(s,length);throw new AssertionError("Expected rejection: "+s);}
    catch(IllegalArgumentException expected){count++;}
  }
  public static void main(String[]args){
    RangePolicy.Selection full=RangePolicy.parse(null,100);
    check(full.status()==200&&full.start==0&&full.end==99&&full.length()==100);
    RangePolicy.Selection first=RangePolicy.parse("bytes=0-19",100);
    check(first.status()==206&&first.start==0&&first.end==19&&first.length()==20);
    check("bytes 0-19/100".equals(first.contentRange()));
    RangePolicy.Selection end=RangePolicy.parse("bytes=90-",100);
    check(end.start==90&&end.end==99);
    RangePolicy.Selection suffix=RangePolicy.parse("bytes=-10",100);
    check(suffix.start==90&&suffix.end==99);
    check(RangePolicy.parse("bytes=0-999",100).end==99);
    check(RangePolicy.parse("bytes=-200",100).start==0);
    invalid("bytes=200-",100);
    invalid("bytes=10-9",100);
    invalid("bytes=-0",100);
    invalid("bytes=0-1,3-4",100);
    invalid("bytes=999999999999999999999999-",100);
    invalid("units=0-20",100);
    invalid("bytes=-",100);
    invalid("bytes=0-0",0);
    System.out.println("PASS "+count+" range + invalid-request regressions");
  }
}