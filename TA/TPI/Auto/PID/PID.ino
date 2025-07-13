const int PIN_INPUT = A0;
const int PIN_OUTPUT = 3;

double Kp=2, Ki=5, Kd=1;

// variables externas del controlador
double Input, Output, Setpoint;
 
// variables internas del controlador
unsigned long currentTime, previousTime;
double elapsedTime;
double error, lastError, cumError, rateError;
 
void setup()
{
  Input = analogRead(PIN_INPUT);
  Setpoint = 100;
}    
 
void loop(){
  
  pidController.Compute();
  
  Input = analogRead(PIN_INPUT);      // leer una entrada del controlador
  Output = computePID(Input);    // calcular el controlador
  delay(100);
  analogWrite(PIN_OUTPUT, Output);      // escribir la salida del controlador
}
 
double computePID(double inp){     
        currentTime = millis();                          // obtener el tiempo actual
        elapsedTime = (double)(currentTime - previousTime);     // calcular el tiempo transcurrido
        
        error = Setpoint - Input;                               // determinar el error entre la consigna y la medición
        cumError += error * elapsedTime;                    // calcular la integral del error
        rateError = (error - lastError) / elapsedTime;       // calcular la derivada del error
 
        double output = kp*error + ki*cumError + kd*rateError;     // calcular la salida del PID
 
        lastError = error;                                    // almacenar error anterior
        previousTime = currentTime;                           // almacenar el tiempo anterior
 
        return output;
}
