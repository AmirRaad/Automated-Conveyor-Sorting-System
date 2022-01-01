#include <Servo.h>

Servo servo_arm;
Servo servo_belt;
int input[2];
int n = 1;

int s_down = 0;     // variable to store the value coming from down sensor.
int s_up = 0;       // variable to store the value coming from up sensor.
bool flag = false;  // boolean value to make belt movment related to begin button in the UI.


void setup() {
  Serial.begin(9600);
  servo_arm.attach(8);
  servo_belt.attach(9);
  // initial values:
  servo_arm.write(90);
  servo_belt.write(90);
  Serial.println("Ready!");

}

void loop() {
  s_down = analogRead(A4);
  s_up = analogRead(A5);
  
  int i = 0;

  while (Serial.available() > 0) {
    char c = Serial.read();
    
    switch(c){
         case('S'): // start case, activates with begin button.
          servo_belt.write(85);
          flag = true;
          delay(50);
          break;

         case('B'): // move belt backwards.
          servo_belt.write(115);
          delay(50);
          break;

         case('X'): // stop belt and reset arm angle.
          servo_belt.write(90);
          servo_arm.write(90);
          delay(50);
          break;
         
        case('A'): // accepted case
        servo_arm.write(120);
        servo_belt.write(85);
        delay(8000);
        servo_belt.write(90);
        break;
             
      case('R'): // rejected case
        servo_arm.write(65);
        servo_belt.write(85);
        delay(8000);
        servo_belt.write(90);
        break;
        
    default:
      Serial.println("x");
    }
    // read manual dial values from UI.
    if (c == 'a'){
      input[0] = readInt('*');
      i++;
    }
    if (c == 's'){
      input[1] = readInt('$');
      i++;
    }
    if (i >= n)
      break;
  }
  if (input[0] >= 65 && input[0] <= 120)
    servo_arm.write(input[0]);
    delay(10);

  if (input[1] >= 80 && input[1] <= 120)
    servo_belt.write(input[1]);
    delay(10);

  if( s_down<40 && s_up>40 && flag){ // one sensor activated.
      
       servo_arm.write(65);
       servo_belt.write(85);
       Serial.write('1');
       delay(10000);
       servo_belt.write(90);
  }
    if(s_down < 40 && s_up < 40 && flag){ // two sensors activated.
      servo_belt.write(85);
      delay(2000);
      servo_belt.write(90);
      delay(500);
      Serial.write('2');
      flag = false;
    }
    
  delay(50);
  // print sensor values on the serial monitor, don't use with the main program (GUI).
  /*if(!(Serial.available())){
  Serial.print("s_down:");
  Serial.print(s_down);
  Serial.print(", s_up:");
  Serial.println(s_up);
  }*/
}

int readInt(char symbol) {
  int ret = 0;
  bool ne = 0;
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '-')
      ne = 1;
    else if (c == symbol) {
      return ne ? -ret : ret;
    } else {
      ret *= 10;
      ret += c - '0';
    }
  }
}
