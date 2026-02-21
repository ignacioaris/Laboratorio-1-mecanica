// ===============================
// Experimento de Caída Libre
// Sensor ultrasónico SRF04
// Recolección de y(t)
// ===============================

const int trigPin = 9;
const int echoPin = 10;

unsigned long t0;
const unsigned long sampleInterval = 30; // ms → ~33 Hz

void setup() {
  Serial.begin(9600);

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  delay(2000); // tiempo para estabilizar

  Serial.println("time_ms,distance_m");
  t0 = millis();
}

void loop() {
  static unsigned long lastSample = 0;
  unsigned long currentTime = millis();

  if (currentTime - lastSample >= sampleInterval) {
    lastSample = currentTime;

    float distance = medirDistancia();
    unsigned long t = currentTime - t0;

    // Evitar valores erráticos
    if (distance > 0.05 && distance < 3.0) {
      Serial.print(t);
      Serial.print(",");
      Serial.println(distance, 4);
    }
  }
}

// ===============================
// Función de medición
// ===============================
float medirDistancia() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duracion = pulseIn(echoPin, HIGH, 30000); // timeout 30 ms

  if (duracion == 0) return -1;

  // Velocidad del sonido ≈ 343 m/s → 0.0343 cm/us
  float distancia = (duracion * 0.0343) / 2.0; // cm
  return distancia / 100.0; // metros
} 
