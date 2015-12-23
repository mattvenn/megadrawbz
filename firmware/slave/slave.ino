typedef struct {
    uint8_t command;
    unsigned int pos;
    uint8_t cksum;
} Slave;

typedef struct {
    uint8_t status;
    unsigned int data;
    uint8_t cksum;
} Response;

//enum SlaveCommand {SLV_LOAD, SLV_SET_POS, SLV_LOAD_P, SLV_LOAD_I, SLV_LOAD_D};
typedef enum {SLV_LOAD, SLV_SET_POS, SLV_LOAD_P, SLV_LOAD_I, SLV_LOAD_D, SLV_GET_POS} SlaveCommand;


#define RS485Transmit    HIGH
#define RS485Receive     LOW

#include "timer.h"
#include "buttons.h"
#include "utils.h"
#include "pindefs.h"
#include <Encoder.h>
Encoder myEnc(ENCA,ENCB);
#include <SoftwareSerial.h>
SoftwareSerial master_serial(SS_RX, SS_TX); // RX, TX

const float mm_to_pulse = 1.6985;

volatile bool calc = false;

//pid globals
int pwm = 128;
#define MAX_POSREF 65535
unsigned int posref = 0;
long curpos = 0;
float b0 = 0;
float b1 = 0;
float b2 = 0;
double yn = 0;
double ynm1 = 0;
float xn = 0;
float xnm1 = 0;
float xnm2 = 0;
float kp = .45;
float ki = 0.000;
float kd = .25;

void setup()
{
    buttons_setup();
    setup_timer2();
    Serial.begin(115200);
    master_serial.begin(57600); // 115200 too fast for reliable soft serial

    pinMode(SSerialTxControl, OUTPUT);  
    digitalWrite(SSerialTxControl, RS485Receive);  // Init Transceiver

    pinMode(FOR, OUTPUT);
    digitalWrite(FOR,LOW);
    pinMode(REV, OUTPUT);
    digitalWrite(REV,LOW);

    pinMode(LED_STATUS, OUTPUT);
    pinMode(LED_ERROR, OUTPUT);
    pinMode(LED_POWER, OUTPUT);
    digitalWrite(LED_POWER, HIGH);


    // pid init
    pid_init();

    // turn on interrupts
    interrupts();

}

void pid_init()
{
    b0 = kp+ki+kd;
    b1 = -kp-2*kd;
    b2 = kd;

    yn = 0;
    ynm1 = 0;
    xn = 0;
    xnm1 = 0;
    xnm2 = 0;
}

int bad_cksum = 0;
int ok = 0;

void loop()
{
    switch(buttons_check())
    {
        case IN:
            if(posref < MAX_POSREF)
                posref ++;
            delay(1);
            break;
        case OUT:
            if(posref > 0)
                posref --;
            delay(1);
            break;
        case HOME:
            /*
            while(buttons_check() != LIMIT)
                drive(HOME_PWM);
            drive(0);
            */
            posref = 0;
            myEnc.write(0);
            break;
    }
    if(calc)
    {
        calc = false;
        digitalWrite(LED_STATUS,HIGH);

        //pid calculation
        curpos = myEnc.read();
        xn = float(posref - curpos);
        yn = ynm1 + (b0*xn) + (b1*xnm1) + (b2*xnm2);
        ynm1 = yn;

        //write pwm values
        drive(yn);

        //set previous input and output values
        xnm1 = xn;
        xnm2 = xnm1;
        digitalWrite(LED_STATUS,LOW);
    }
    if(master_serial.available() >= sizeof(Slave))
    {
        Slave data;
        char buf[sizeof(Slave)];
        // do something with status?
        int status = master_serial.readBytes(buf, sizeof(Slave));

        //copy buffer to structure
        memcpy(&data, &buf, sizeof(Slave));
        //calculate cksum is ok
        if(data.cksum != CRC8(buf,sizeof(Slave)-1))
        {
            //ignore broken packet
            bad_cksum ++;
            //Serial.println("bad cksum");
            return;
        }
        //Serial.println("ok!");
        //set the servo position
        switch(data.command)
        {
            case SLV_LOAD:
                //Serial.print("loaded:");
                //Serial.println(data.pos);
                ok ++;
                posref = data.pos * mm_to_pulse;
                break;
            case SLV_SET_POS:
                //Serial.print("setpos:");
                //Serial.println(data.pos);
                posref = data.pos * mm_to_pulse;
                myEnc.write(posref);
                break;
            case SLV_LOAD_P:
                kp = data.pos / 1000.0;
                pid_init();
                break;
            case SLV_LOAD_I:
                ki = data.pos / 1000.0;
                pid_init();
                break;
            case SLV_LOAD_D:
                kd = data.pos / 1000.0;
                pid_init();
                break;
            case SLV_GET_POS:
                send_response(SLV_GET_POS, curpos / mm_to_pulse);
                //Serial.println("sent pos");
                break;
                
                
        }
    }
    /*
    leaving this in seems to stop the servo from taking new serial commands until the serial monitor is opened 
    if(Serial.available())
    {
        char cmd = Serial.read();
        switch(cmd)
        {
            case 'a':
                Serial.println(ok);
                Serial.println(bad_cksum);
                break;
            case 'b':
                ok = 0;
                bad_cksum = 0;
                break;
        }
    }
    */
}

void send_response(uint8_t status, unsigned int data)
{
    //wait for master to release rs485 control line
    delay(2);
    Response resp;
    resp.status = status;
    resp.data = data;

    char buf[sizeof(Response)];
    memcpy(&buf, &resp, sizeof(Response));
    resp.cksum = CRC8(buf,sizeof(Response)-1);

    memcpy(&buf, &resp, sizeof(Response));

    // Enable RS485 Transmit    
    digitalWrite(SSerialTxControl, RS485Transmit);  
    delay(1);

    for(int b = 0; b < sizeof(Response); b++)
        master_serial.write(buf[b]);

    master_serial.flush(); // remove this as it will block?
    delay(1);
    // Disable RS485 Transmit      
    digitalWrite(SSerialTxControl, RS485Receive); 
}
