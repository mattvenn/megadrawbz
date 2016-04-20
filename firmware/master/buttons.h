#ifndef buttons_h
#define buttons_h

#include "Arduino.h"

#define HOME_PWM -70

enum ButtonStatus { B_IN, B_OUT, B_HOME, B_NONE };

#define BUT_IN A0
#define BUT_OUT A1
#define BUT_HOME A2
#define BUT_LIMIT A3

void buttons_setup();
bool check_limit();
enum ButtonStatus buttons_check();

#endif
