#include <Wire.h>
#include <L3G.h>
#include <FileIO.h>

double dat = 0b11101111;
double acrt = 0b00100000;
double CTRL4adr = 0b00100011;
//maxime habryn et matthieu hugny
L3G gyro;
int cal_int;
int cal_nb = 4000;
int percentage;
double gyro_pitch, gyro_roll, gyro_yaw;
double gyro_roll_cal, gyro_pitch_cal, gyro_yaw_cal;


void setup() {
  Serial.begin(250000);
  Wire.begin();
  FileSystem.begin();
 
  while(!gyro.init())
  {
    Serial.println("Failed to autodetect gyro type!");
    delay(400);
  }
  //printtofile("t;x;y;z" );
  
  gyro.enableDefault();

  //0x20 CTRL1
  //111011111
  Serial.print("0x20 : ");
  Serial.println(gyro.readReg(acrt));
  
  gyro.writeReg(acrt,dat);
  Serial.print("0x20 apres: ");
  Serial.println(gyro.readReg(acrt));

  Serial.print("0x23 apres: ");
  Serial.println(gyro.readReg(CTRL4adr));
  
  delay(1000);
  Serial.print("Starting calibration..."); 

  for (cal_int = 0; cal_int < 4000 ; cal_int ++) {   //Take 4000 readings for calibration
    gyro.read();                                //Read the gyro output
    gyro_roll_cal += gyro.g.x;                      //Ad roll value to gyro_roll_cal
    gyro_pitch_cal += gyro.g.y;                    //Ad pitch value to gyro_pitch_cal
    gyro_yaw_cal += gyro.g.z;                        //Ad yaw value to gyro_yaw_cal
    if (cal_int % 100 == 0){
      Serial.print((cal_int*100/4000));
      Serial.println("%");
    }
    delay(4);                                        //Wait 4 milliseconds before the next loop
  }
  Serial.println("done!");                          //2000 measures are done!
  gyro_roll_cal /= 4000;                             //Divide the roll total by 2000
  gyro_pitch_cal /= 4000;                            //Divide the pitch total by 2000
  gyro_yaw_cal /= 4000;                              //Divide the yaw total by 2000
  Serial.println("S");
}

void disp(double x,double y,double z){
  Serial.print((double)x);
  Serial.print(" ");
  Serial.print((double)y);
  Serial.print(" ");
  Serial.println((double)z);
}

void loop() {
  gyro.read();
  gyro_roll = (gyro.g.x - gyro_roll_cal);//57.14286;
  gyro_pitch = (gyro.g.y - gyro_pitch_cal);//57.14286;
  gyro_yaw = (gyro.g.z - gyro_yaw_cal);//57.14286;   
  disp(gyro_roll,gyro_pitch,gyro_yaw);
  //printtofile(getTimeStamp() + ";" + String(gyro_roll)+ ";" + String(gyro_roll)+ ";" + String(gyro_roll)+ ";" );
  delay(4);
}

String getTimeStamp() {
  String result;
  Process time;
  // date is a command line utility to get the date and the time
  // in different formats depending on the additional parameter
  time.begin("date");
  time.addParameter("+%D-%T");  // parameters: D for the complete date mm/dd/yy
  //             T for the time hh:mm:ss
  time.run();  // run the command

  // read the output of the command
  while (time.available() > 0) {
    char c = time.read();
    if (c != '\n') {
      result += c;
    }
  }

  return result;
}
