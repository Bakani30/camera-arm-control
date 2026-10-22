# ราคามอเตอร์ผสม PWM + bus: สำรวจไทย 2026-10-02

ผู้ใช้ยืนยัน **3,000 บาท ± เป็นงบมอเตอร์เท่านั้น**; controller/PSU/งานพิมพ์แยก แต่กรอบฮาร์ดแวร์รวมเดิม 10,000 บาทยังอยู่ รายการนี้เป็นตัวอย่างคำนวณ ไม่ได้เลือกมอเตอร์หรือรับรองว่ารับโหลดแขน/บล็อกได้ ทุกการทดลอง **NOT RUN**

## ราคาหน้าร้านไทย

ราคาต่อหนึ่งตัว ณ ตรวจ; หน้าสินค้าระบุพร้อมส่ง แต่ยังไม่ได้ตรวจจำนวนคงเหลือ ค่าส่ง/ยอดภาษีสุดท้าย/อุปกรณ์ประกอบจริง ต้องยืนยันตอนจัด BOM ไม่ใช้คูปองหรือราคาเริ่มต้นหลาย variant ในการคำนวณ

| รุ่นที่ร้านระบุ | บาท/ตัว | หน้าร้าน/variant |
|---|---:|---|
| MG996R 0–180° เฟืองโลหะ | 175 | [CyberTice RA004](https://www.cybertice.com/product/63/mg996r-servo-motor-0-180-องศา-เฟืองโลหะทั้งหมด); พร้อมส่ง อัปเดต 29 ก.ย. 2569; แยกจากรุ่น 360° continuous RA043 |
| TD-8120MG 0–270° เฟืองโลหะ | 480 | [CyberTice RA111](https://www.cybertice.com/product/3787/td-8120mg-servo-motor-0-270องศา-เฟืองโลหะทั้งหมด-แรงบิดสูงสุด-20kg); พร้อมส่ง; positional PWM ตามรายการร้าน ใช้เป็นตัวแทนระดับ DS3218/TD8120 เท่านั้น ไม่ถือว่ามีสเปกผู้ผลิต DS3218 |
| MG90S up to 180° | 75 | [Arduitronics AG00005](https://www.arduitronics.com/product/53/micro-servo-mg90s-up-to-180-degree); พร้อมส่ง; ตัวเลือกก้าม/ข้อมือที่ยังต้องคำนวณโหลด ไม่ใช่รุ่นหมุนต่อเนื่อง |
| SG90 90–180° | 64 | [Arduitronics AG00006](https://www.arduitronics.com/product/283/micro-servo-sg90-90-180-degree); พร้อมส่ง; ไม่ใช่ AG30006 360° continuous |
| SC15 serial bus | 1,185 | [Arduitronics AG00691](https://www.arduitronics.com/product/5144/sc15-17kg-large-torque-programmable-serial-bus-servo-แท้จาก-waveshare); พร้อมส่ง ร้านระบุ Waveshare; หน้าขายไม่รวม bus driver board/PSU |

**อย่าถือชื่อ MG996R/MG90S ว่ารับรองสินค้าแท้หรือสเปกเดียวกัน:** ตัวอย่าง MG996R ร้านไทยกล่าวถึง 15 kg·cm/4.8–7.2V แต่ [TowerPro ผู้ผลิต](https://towerpro.com.tw/product/mg996r/) ระบุ 11 kg·cm ที่ 6V/4.8–6.6V และคำตอบผู้ผลิตระบุ travel 0–159° สำหรับรุ่นบนหน้านั้น จึงใช้ 175 บาทเป็นราคา SKU ร้านที่อ้าง 180° เท่านั้น ไม่ยกสเปกผู้ผลิตมารับรองล็อตร้าน ความแม่นยำจริง/แรงบิดต่อเนื่อง/ของแท้ยังไม่ตรวจ

## ตัวอย่างเฉพาะมอเตอร์

สมมติหนึ่งมอเตอร์ต่อแกนและหนึ่งตัวก้าม; จำนวนนี้ยังไม่ใช่ topology ที่ผ่านตรวจ หรือจำนวนมอเตอร์ที่แบบแขนจริงต้องใช้

| ข้อเสนอ | คำนวณ THB | feedback ที่มี |
|---|---|---|
| A: **6 แกนแขน + ก้าม**, bus สองข้อ | 2×1,185 + 4×175 + 75 = **3,145** | มุมวัดจาก SC15 สองข้อ; PWM สี่ข้อ+ก้ามยังไม่มีมุมวัดกลับตาม interface มาตรฐาน |
| B: **5 แกนแขน + ก้าม**, bus สองข้อ | 2×1,185 + 3×175 + 75 = **2,970** | เหมือน A แต่แขนลดหนึ่งแกน เป็นทางเลือกที่ต้องตกลงเป้าหมาย pose ไม่ใช่ลดเป้าหมายเดิมเงียบ ๆ |
| C: **6 แกนแขน + ก้าม**, bus หนึ่งข้อ + PWM ระดับสูงสามข้อ | 1,185 + 3×480 + 2×175 + 75 = **3,050** | มุมวัดเพียงหนึ่งข้อ; TD8120MG ที่แรงกว่าในคำกล่าวร้านไม่ได้เพิ่ม readback อัตโนมัติ |

หากเปลี่ยนก้าม MG90S เป็น SG90 ลด 11 บาทต่อชุด แต่ยังไม่มีหลักฐานว่าแรงจับพอ ข้อต่อ bus ควรอยู่ข้อใดต้องพิจารณาทั้งแรงบิด ผลต่อความคลาดเคลื่อน และ failure ที่ต้องวัด ไม่อ้างว่าเอา feedback ไปฐาน/ไหล่แล้วรู้ pose จริงของแขนทั้งหมด บล็อก วัสดุ น้ำหนักปลายแขน ความยาวลิงก์ เกียร์ทด backlash และ moment arm ต้องกำหนดก่อนเลือก

## การเชื่อมและไฟ

- [Waveshare SC15 ผู้ผลิต](https://www.waveshare.com/product/robotics/motors-servos/sc15-servo.htm) และ [wiki/API](https://www.waveshare.com/wiki/SC15_Servo) ยืนยัน TTL bus, feedback position/load/speed/input voltage และแยก positional servo mode จาก continuous motor mode; **ไม่ใช่สั่งองศาผ่าน PWM ธรรมดา** ผู้ผลิตปัจจุบันระบุ 210°/1024 แต่ร้านไทยระบุ 180°/1024 ต้องตรวจ revision/limits ก่อน calibration
- PWM และ TTL bus ควบคุมร่วมในโปรแกรมทีมได้ในเชิงสถาปัตยกรรมผ่าน adapter แยก แต่ **ยังไม่ IMPLEMENTED** ใช้ timestamps/units/joint mapping เดียวกัน; ค่าพัลส์หรือมุม command ไม่ใช่ measured angle การอ่าน register PCA9685 ไม่ได้เพิ่มเซนเซอร์มุม: [NXP](https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf) ระบุหน้าที่สร้าง PWM
- SC15 ผู้ผลิตระบุ 4.8–8.4V; ST3215 มีทั้ง 7.4V และ 12V ใน [ตารางผู้ผลิต](https://www.waveshare.com/product/robotics/st3215-servo.htm) จึงไม่ใช้ชื่อรุ่นตัดสินไฟ เมื่อต้องใช้ bus rail แรงดันสูงกว่า PWM ที่เลือก ต้องแยกราง/แปลงไฟพร้อม ground/reference ตามวงจรที่ตรวจ **ห้ามถือว่า SC15 ที่ 8.4V หรือ ST ที่ 12V ต่อไฟร่วมกับ MG996R ได้** และไม่ถือว่า PSU ตัวอย่างด้านล่างพอกับ peak current โดยยังไม่คำนวณ

## ค่าอุปกรณ์แยกจาก 3,000 บาท

ตัวอย่างราคา ไม่ใช่ BOM อนุมัติ; ทุกหน้าระบุพร้อมส่ง ราคาไม่รวมค่าส่งที่ยืนยัน:

- [Nano ATmega328P CH340G Type-C B0091](https://www.cybertice.com/product/5696/arduino-nano-3-0-atmega328p-type-c-usb-รุ่นใหม่ชิฟ-ch340g-แบบบัดกรีขา-ไม่มีสาย-usb): **140 บาท**, ไม่มีสาย USB; หรือ [ESP32-B Type-C M1673](https://www.cybertice.com/product/5693/esp32-nodemcu-บอร์ดพัฒนา-esp32-b-usb-type-c-black-esp32-dev-board): **265 บาท**; ไม่ต้องซื้อทั้งคู่โดยอัตโนมัติ
- [PCA9685 SG00237](https://www.arduitronics.com/product/1589/pca9685-16-channel-module-pwm-servo-drive-board-robot-controller-h5b4-compatible-บอร์ดสำหรับขับ-serv): **265 บาท**, optional PWM driver; ไม่ขับ bus servo ผ่าน PCA9685
- [Bus Servo Adapter(A) AG00810](https://www.arduitronics.com/product/6119/serial-bus-servo-driver-board-integrates-servo-power-supply-and-control-circuit-applicable-for-st-sc): **345 บาท**, PSU แยก; ต้องตรวจ host connection/circuit และรุ่น bus ให้ตรง
- [PSU 5V 10A P0017](https://www.cybertice.com/product/559/switching-power-supply-แหล่งจ่ายไฟ-สวิตชิ่งเพาเวอร์ซัพพลาย-5v-10a): **325 บาท**; ราคาอ้างอิง ไม่รับรองว่าเพียงพอหรือใช้แทนทุก rail ได้ ยังไม่รวม enclosure/สาย/ฟิวส์/วิธีหยุด/ฮอร์น/ลูกปืน/โครง/อะไหล่

## unresolved และผลตรวจ

ค้นเฉพาะร้านไทยและหน้าผู้ผลิต: **DS3218 ราคาตรง variant, SC09 ราคาไทย และ STS3215 ราคาไทยยัง unresolved** [DroneTh มีหน้าสินค้า STS3215 7.4V](https://droneth.or.th/product/feetech-sts3215-74v-servo/) แต่ไม่เผยราคาตัวเลข ต้องสอบถาม; งานนี้ไม่ได้ติดต่อผู้ขาย ไม่ใช้ราคาต่างประเทศ/marketplace ที่ variant ไม่ชัดมาเติม

ตรวจ arithmetic และ URL จากหน้าผู้ขาย/ผู้ผลิตแบบ read-only; ไม่สั่งซื้อ ติดตั้ง พิมพ์ หรือขยับแขน ยังไม่มีผลรับโหลด/ความแม่นยำ/latency/feedback integration งานต่อ: เลือก geometry และแกนที่ต้องวัด → คำนวณ torque margin/limits/ไฟ → ตรวจ SKU และ BOM รวมไม่เกินกรอบโครงการ → ค่อยวางการทดลอง
