/* Independent read-only UIM observer. See the SIM detection reference for ABI and permission limits. */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <dlfcn.h>
#include <sys/system_properties.h>
#include <time.h>
#include <signal.h>
typedef void*(*svc_fn)(int,int,int);
typedef void(*ind_fn)(void*,unsigned,void*,unsigned,void*);
typedef int(*init_fn)(void*,unsigned,ind_fn,void*,void*,unsigned,void**);
typedef int(*raw_fn)(void*,unsigned,void*,unsigned,void*,unsigned,unsigned*,unsigned);
typedef int(*release_fn)(void*);
static unsigned le32(const unsigned char*p){return p[0]|((unsigned)p[1]<<8)|((unsigned)p[2]<<16)|((unsigned)p[3]<<24);}
static void parse(unsigned msg,const unsigned char*b,unsigned n){
 unsigned p=0;
 while(p+3<=n){unsigned type=b[p],len=b[p+1]|(b[p+2]<<8);p+=3;if(len>n-p){puts("MALFORMED_TLV");return;}const unsigned char*v=b+p;
  if(type==2&&len==4)printf("RESULT=%u ERROR=%u\n",v[0]|(v[1]<<8),v[2]|(v[3]<<8));
  if((msg==0x2f||msg==0x32)&&type==0x10&&len>=15){
   printf("CARD_COUNT=%u GW_PRIMARY_INDEX=%u GW_SECONDARY_INDEX=%u\n",v[8],v[0]|(v[1]<<8),v[4]|(v[5]<<8));
   // Both slots' non-identity states. No AID, PIN or ICCID output.
   unsigned q=9;
   for(unsigned slot=0;slot<v[8]&&slot<8;slot++){
    if(q+6>len)break;
    unsigned state=v[q],error=v[q+4],apps=v[q+5];q+=6;
    printf("SLOT%u_CARD_STATE=%u SLOT%u_CARD_ERROR=%u SLOT%u_APP_COUNT=%u ERROR_STATE_ACTIVE=%u\n",slot+1,state,slot+1,error,slot+1,apps,state==2);
    for(unsigned app=0;app<apps&&app<16;app++){
     if(q+7>len)break;unsigned aid_len=v[q+6];if(q+14+aid_len>len)break;
     printf("SLOT%u_APP=%u TYPE=%u STATE=%u PERSONALIZATION_STATE=%u\n",slot+1,app,v[q],v[q+1],v[q+2]);q+=14+aid_len;
    }
   }
  }
  if((msg==0x47||msg==0x48)&&type==0x10&&len>=1){
   unsigned q=1,count=v[0];printf("PHYSICAL_SLOT_COUNT=%u\n",count);
   for(unsigned slot=0;slot<count;slot++){
    if(q+10>len){puts("SHORT_SLOT_STATUS");break;}
    unsigned card=le32(v+q),active=le32(v+q+4),logical=v[q+8],iccid_len=v[q+9];q+=10;
    printf("SLOT=%u PHYSICAL_CARD_STATE=%u SLOT_STATE=%u LOGICAL_SLOT=%u ICCID_PRESENT=%u\n",slot+1,card,active,logical,iccid_len>0);
    if(iccid_len>len-q)break;q+=iccid_len;
   }
  }
  if((msg==0x47||msg==0x48)&&type==0x11&&len>=1){
   unsigned q=1,count=v[0];
   for(unsigned slot=0;slot<count;slot++){
    if(q+6>len)break;unsigned protocol=le32(v+q),apps=v[q+4],atr_len=v[q+5];q+=6;
    if(atr_len>len-q||q+atr_len+1>len)break;q+=atr_len;
    printf("SLOT=%u PROTOCOL=%u VALID_APPLICATIONS=%u ATR_BYTES=%u EUICC=%u\n",slot+1,protocol,apps,atr_len,v[q++]);
   }
  }
  p+=len;
 }
}
static volatile sig_atomic_t stopping=0;
static void stop_handler(int sig){(void)sig;stopping=1;}
static void report(const char*kind,unsigned msg,const unsigned char*b,unsigned len){
 struct timespec t;clock_gettime(CLOCK_REALTIME,&t);flockfile(stdout);
 printf("EVENT=%s MSG=%x EPOCH=%lld.%03ld BYTES=%u\n",kind,msg,(long long)t.tv_sec,t.tv_nsec/1000000,len);parse(msg,b,len);funlockfile(stdout);
}
static void indication(void*handle,unsigned msg,void*buf,unsigned len,void*cookie){
 (void)handle;(void)cookie;if(msg==0x32||msg==0x48)report("INDICATION",msg,buf,len);
}
int main(int argc,char**argv){
 int observe=argc==2&&!strcmp(argv[1],"--observe");if(argc>1&&!observe)return 2;
 setbuf(stdout,NULL);alarm(observe?620:25);signal(SIGTERM,stop_handler);signal(SIGINT,stop_handler);char serial[PROP_VALUE_MAX]={0};__system_property_get("ro.serialno",serial);const char*target=getenv("PORT8T_SERIAL");if(!target||!*target||strcmp(serial,target))return 2;
 const char*dir=getenv("PORT8T_QMI_LIBDIR");if(!dir||dir[0]!='/')return 2;char cp[4096],sp[4096];if(snprintf(cp,sizeof(cp),"%s/libqmi_cci.so",dir)>=(int)sizeof(cp)||snprintf(sp,sizeof(sp),"%s/libqmiservices.so",dir)>=(int)sizeof(sp))return 2;
 void*c=dlopen(cp,RTLD_NOW|RTLD_LOCAL);void*s=dlopen(sp,RTLD_NOW|RTLD_LOCAL);
 if(!c||!s){printf("DLOPEN_ERROR=%s\n",dlerror());return 3;}
 svc_fn svc=(svc_fn)dlsym(s,"uim_get_service_object_internal_v01");init_fn init=(init_fn)dlsym(c,"qmi_client_init_instance");raw_fn raw=(raw_fn)dlsym(c,"qmi_client_send_raw_msg_sync");release_fn release=(release_fn)dlsym(c,"qmi_client_release");if(!svc||!init||!raw||!release)return 4;
 void*object=svc(1,0x62,6);if(!object)return 5;void*client=NULL;void*os_params=calloc(1,2048);if(!os_params)return 5;
 int rc=init(object,0xffff,observe?indication:NULL,NULL,os_params,7000,&client);printf("UIM_INIT=%d\n",rc);if(rc||!client)return 6;
 if(observe){
  // Notification mask is scoped to this new QMI client, not RIL's callbacks.
  unsigned char mask[]={1,4,0,17,0,0,0},response[128]={0};unsigned len=0;
  rc=raw(client,0x2e,mask,sizeof(mask),response,sizeof(response),&len,4000);
  printf("REGISTER_OWN_CLIENT_EVENTS_TRANSPORT=%d\n",rc);if(!rc)report("REGISTER",0x2e,response,len);
 }
 unsigned ids[]={0x2f,0x47};
 for(unsigned i=0;i<2;i++){unsigned char response[8192]={0};unsigned len=0;rc=raw(client,ids[i],NULL,0,response,sizeof(response),&len,4000);printf("READONLY_MESSAGE=%x TRANSPORT=%d RESPONSE_BYTES=%u\n",ids[i],rc,len);if(!rc&&len<=sizeof(response))report("QUERY",ids[i],response,len);}
 if(observe){puts("UIM_WATCH_READY");for(unsigned i=0;i<600&&!stopping;i++)sleep(1);puts("UIM_WATCH_FINISHED");}
 release(client);free(os_params);return 0;
}
