# Modified from https://github.com/DFRobot/DFRobot_BMI160/blob/6abe9dc9ed817a806c1a143ff6adc92a2c4e9985/python/raspberrypi/DFRobot_BMI160.py to support MicroPython I2C communication on the Pi Pico, fix several bugs, and add FIFO support. New or modified code is shown below:

# Replace all imports with
from time import sleep
from ustruct import unpack_from

''' FIFO config '''
BMI160_FIFO_GYR_EN = 0x80
BMI160_FIFO_ACC_EN = 0x40
BMI160_FIFO_MAG_EN = 0x20
BMI160_FIFO_HEADER_EN = 0x10
BMI160_FIFO_TIME_EN = 0x02

class DFRobot_BMI160:
  def __init__(self):
    pass

  def soft_reset(self):
    '''
      @brief Soft reset
      @return Error code:
      @n      BMI160_OK     or  0 : Soft reset succeeded
      @n      others value        : Soft reset failed
    '''
    rslt = self._set_regs(BMI160_COMMAND_REG_ADDR, [BMI160_SOFT_RESET_CMD])
    sleep(BMI160_SOFT_RESET_DELAY_MS)
    if rslt == BMI160_OK:
      self._default_param_settg()
    return rslt

  def _get_raw_data(self):
    self._raw_data = [0]*BMI160_RAW_DATA_LENGTH
    rslt = self._get_regs(BMI160_GYRO_DATA_ADDR, BMI160_RAW_DATA_LENGTH)
    self._update = 0x03
    index = 1
    _gyro_x  = 0
    _gyro_y  = 0
    _gyro_z  = 0
    _accel_x = 0
    _accel_y = 0
    _accel_z = 0
    _accel_sensor_time = 0
    _gyro_sensor_time  = 0
    if rslt[0] == BMI160_OK:
      self._gyro_x, self._gyro_y, self._gyro_z, self._accel_x, self._accel_y, self._accel_z = unpack_from("<hhhhhh", bytes(rslt), index) # Parse little-endian int16
      index += 2*6

      time_0 = rslt[index]
      time_1 = rslt[index+1] << 8
      time_2 = rslt[index+2] << 16

      self._accel_sensor_time = time_2|time_1|time_0
      self._gyro_sensor_time = time_2|time_1|time_0
      return BMI160_OK
    return BMI160_E_COM_FAIL

  def _set_regs(self, reg, dataList):
    rslt = BMI160_OK
    count = 0
    rslt = self._write_bytes(reg, dataList)
    sleep(0.001)
    if rslt == len(dataList):
      return BMI160_OK
    else:
      return BMI160_E_COM_FAIL

  def _get_regs(self, reg, length):
    rslt = self._read_bytes(reg,length)
    sleep(0.001)
    if len(rslt) != length:
      rslt.insert(0, BMI160_E_COM_FAIL)
    else:
      rslt.insert(0, BMI160_OK)
    return rslt

  def _set_accel_conf(self):
    rslt = self._check_accel_config()
    if rslt[0] == BMI160_OK:
      rslt1 = self._set_regs(BMI160_ACCEL_CONFIG_ADDR, [rslt[1]])
      if rslt1 == BMI160_OK:
        self._dev_pre_accel_cfg_bw    = self._dev_accel_cfg_bw
        self._dev_pre_accel_cfg_odr   = self._dev_accel_cfg_odr
        sleep(BMI160_ONE_MS_DELAY)
        rslt1 = self._set_regs(BMI160_ACCEL_RANGE_ADDR, [rslt[2]])
        if rslt1 == BMI160_OK:
          self._dev_pre_accel_cfg_range = self._dev_accel_cfg_range
    else:
      rslt1 = rslt[0]
    return rslt1

  def _set_gyro_conf(self):
    value = [0]*2
    rslt = self._check_gyro_config()
    if rslt[0] == BMI160_OK:
      value[0] = rslt[1]
      value[1] = rslt[2]
      rslt = self._set_regs(BMI160_GYRO_CONFIG_ADDR, [value[0]])
      if rslt == BMI160_OK: 
        self._dev_pre_gyro_cfg_bw    = self._dev_gyro_cfg_bw
        self._dev_pre_gyro_cfg_odr   = self._dev_gyro_cfg_odr
        sleep(BMI160_ONE_MS_DELAY)
        rslt = self._set_regs(BMI160_GYRO_RANGE_ADDR, [value[1]])
        if rslt == BMI160_OK:
          self._dev_pre_gyro_cfg_range = self._dev_gyro_cfg_range
    else:
      rslt = rslt[0]
    return rslt

  def _set_accel_pwr(self):
    rslt = BMI160_OK
    if (self._dev_accel_cfg_power >= BMI160_ACCEL_SUSPEND_MODE) and (self._dev_accel_cfg_power <= BMI160_ACCEL_LOWPOWER_MODE):
      if self._dev_accel_cfg_power != self._dev_pre_accel_cfg_power:
        rslt = self._process_under_sampling()
        if rslt == BMI160_OK:
          rslt = self._set_regs(BMI160_COMMAND_REG_ADDR, [self._dev_accel_cfg_power])
          if self._dev_pre_accel_cfg_power == BMI160_ACCEL_SUSPEND_MODE:
            sleep(BMI160_ACCEL_DELAY_MS)
          self._dev_pre_accel_cfg_power = self._dev_accel_cfg_power
          return BMI160_OK
    return rslt

  def _set_gyro_pwr(self):
    rslt = BMI160_OK
    if self._dev_gyro_cfg_power == BMI160_GYRO_SUSPEND_MODE or self._dev_gyro_cfg_power == BMI160_GYRO_NORMAL_MODE or self._dev_gyro_cfg_power == BMI160_GYRO_FASTSTARTUP_MODE:
      if self._dev_gyro_cfg_power != self._dev_pre_gyro_cfg_power:
        rslt = self._set_regs(BMI160_COMMAND_REG_ADDR, [self._dev_gyro_cfg_power])
        if self._dev_pre_gyro_cfg_power == BMI160_GYRO_SUSPEND_MODE:
          sleep(BMI160_GYRO_DELAY_MS)
        elif self._dev_pre_gyro_cfg_power == BMI160_GYRO_FASTSTARTUP_MODE and self._dev_gyro_cfg_power == BMI160_GYRO_NORMAL_MODE:
          sleep(0.01)
        self._dev_pre_gyro_cfg_power = self._dev_gyro_cfg_power
        return BMI160_OK
    return rslt

  def _check_gyro_config(self):
    value = [0]*3
    rslt = self._get_regs(BMI160_GYRO_CONFIG_ADDR, 2)
    if rslt[0] == BMI160_OK:
      value[1] = rslt[1]
      value[2] = rslt[2]
      rslt = self._process_gyro_odr(value[1])
      if rslt[0] == BMI160_OK:
        value[1] = rslt[1]
        rslt = self._process_gyro_bw(value[1])
        if rslt[0] == BMI160_OK:
          value[1] = rslt[1] # Hopefully fix issue
          rslt = self._process_gyro_range(value[2])
          if rslt[0] == BMI160_OK:
            value[2] = rslt[1]
    value[0] = rslt[0]
    return value

  def _check_accel_config(self):
    value = [0]*3
    rslt = self._get_regs(BMI160_ACCEL_CONFIG_ADDR, 2)
    if rslt[0] == BMI160_OK:
      value[1] = rslt[1]
      value[2] = rslt[2]
      rslt = self._process_accel_odr(value[1])
      if rslt[0] == BMI160_OK:
        value[1] = rslt[1]
        rslt = self._process_accel_bw(value[1])
        if rslt[0] == BMI160_OK:
          value[1] = rslt[1] # Hopefully fix issue
          rslt = self._process_accel_range(value[2])
          if rslt[0] == BMI160_OK:
            value[2] = rslt[1]
    value[0] = rslt[0]
    return value

class BMI160_I2C(DFRobot_BMI160):
  def __init__(self, i2c, addr = BMI160_IIC_ADDR_SDO_H):
    '''
      @brief The constructor of the BMI160 sensor using I2C communication.
      @param i2c:  The machine.I2C object used for communication.
      @param addr:  7-bit I2C address, controlled by SDO pin.
      @n     BMI160_IIC_ADDR_SDO_H or 0x69:  SDO pull high.(default)
      @n     BMI160_IIC_ADDR_SDO_L or 0x68:  SDO pull down.
    '''
    self._addr = addr
    self._i2c = i2c
    DFRobot_BMI160.__init__(self)

  def _write_bytes(self, reg, buf):
    try:
      self._i2c.writeto_mem(self._addr, reg, bytes(buf))
      return len(buf)
    except Exception as e:
      return 0

  def _read_bytes(self, reg, length):
    try:
      rslt = self._i2c.readfrom_mem(self._addr, reg, length)
      return list(rslt)
    except:
      return [0]*length

  def configure_fifo(self, freq=1600):
    #self._set_regs(BMI160_FIFO_DOWN_ADDR, [0x00]) # Use unfiltered data (Default is 0x88 which is filtered data with no downsampling)
    #self._dev_accel_cfg_bw = BMI160_ACCEL_BW_OSR4_AVG1 # Strong low-pass filter (doesn't seem to affect ODR)
    #self._dev_gyro_cfg_bw = BMI160_GYRO_BW_OSR4_MODE

    # For header mode, fifo data uses independent sensor sampling rate.
    # For headerless, fifo data uses minimum sensor sampling rate (instead of raising error as per datasheet)

    if freq == 1600:
      self._dev_gyro_cfg_odr = BMI160_GYRO_ODR_1600HZ # Reduce gyro odr to same rate since it affects the filter cutoff frequency
      #self._dev_accel_cfg_odr = BMI160_ACCEL_ODR_1600HZ
    elif freq == 100:
      self._dev_gyro_cfg_odr = BMI160_GYRO_ODR_100HZ
      self._dev_accel_cfg_odr = BMI160_ACCEL_ODR_100HZ

    self._set_accel_conf()
    self._set_gyro_conf()

  def enable_fifo(self, header_mode=False):
    config = BMI160_FIFO_GYR_EN | BMI160_FIFO_ACC_EN
    if header_mode:
      config |= BMI160_FIFO_HEADER_EN | BMI160_FIFO_TIME_EN
    return self._set_regs(BMI160_FIFO_CONFIG_1_ADDR, [config])

  def disable_fifo(self):
    return self._set_regs(BMI160_FIFO_CONFIG_1_ADDR, [0])

  @micropython.native
  def get_fifo_byte_counter(self):
    data = self._i2c.readfrom_mem(self._addr, BMI160_FIFO_LENGTH_ADDR, 2)
    return (data[1] & 0x7) << 8 | data[0]

  def clear_fifo():
    BMI160_FIFO_FLUSH = 0xB0
    return self._set_regs(BMI160_COMMAND_REG_ADDR, [BMI160_FIFO_FLUSH])

  @micropython.native
  def read_fifo_into(self, sample_count, mv):
    '''Reads sample_count headerless accel+gyro samples from the FIFO into the memoryview'''
    i2c = self._i2c
    i = 0
    while i < sample_count:
      ready_count = self.get_fifo_byte_counter()
      if ready_count >= 12:
        if ready_count > (sample_count - i) * 12:
          ready_count = (sample_count - i) * 12
        #i2c.readfrom_mem_into(self._addr, BMI160_FIFO_DATA_ADDR, mv[i*12:i*12 + ready_count])
        i2c.readfrom_mem_into(0x69, 0x24, mv[i*12:i*12 + ready_count])
        i += ready_count // 12
