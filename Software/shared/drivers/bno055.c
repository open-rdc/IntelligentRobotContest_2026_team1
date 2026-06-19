#include <stdio.h>
#include "bno055.h"

// レジスタアドレス
static const uint8_t REG_CHIP_ID     = 0x00;
static const uint8_t REG_PAGE_ID     = 0x07;
static const uint8_t REG_EUL_YAW     = 0x1A;
static const uint8_t REG_LIA_X       = 0x28;
static const uint8_t REG_OPR_MODE    = 0x3D;
static const uint8_t REG_PWR_MODE    = 0x3E;
static const uint8_t REG_SYS_TRIGGER = 0x3F;

// 動作モード
static const uint8_t OPR_CONFIG = 0x00;
static const uint8_t OPR_NDOF   = 0x0C;  // 9軸フュージョン

static const uint8_t CHIP_ID_EXPECTED = 0xA0;

static i2c_inst_t *i2c = NULL;

// --- I2C低レベル操作 ---

static void write_reg(uint8_t reg, uint8_t val) {
    uint8_t buf[2] = {reg, val};
    i2c_write_blocking(i2c, BNO055_ADDR, buf, 2, false);
}

static int read_regs(uint8_t reg, uint8_t *buf, size_t len) {
    if (i2c_write_blocking(i2c, BNO055_ADDR, &reg, 1, true) < 0) return -1;
    return i2c_read_blocking(i2c, BNO055_ADDR, buf, len, false);
}

// 6バイト(3軸×16bit)を読み出してfloatベクトルに変換
static bool read_vec3(uint8_t reg, float scale, bno055_vec3_t *out) {
    uint8_t buf[6];
    if (read_regs(reg, buf, 6) < 0) return false;
    out->x = (int16_t)((buf[1] << 8) | buf[0]) / scale;
    out->y = (int16_t)((buf[3] << 8) | buf[2]) / scale;
    out->z = (int16_t)((buf[5] << 8) | buf[4]) / scale;
    return true;
}

// --- 公開API ---

bool bno055_init(i2c_inst_t *i2c_port) {
    i2c = i2c_port;

    // チップID確認
    uint8_t chip_id = 0;
    if (read_regs(REG_CHIP_ID, &chip_id, 1) < 0 || chip_id != CHIP_ID_EXPECTED) {
        printf("BNO055: チップID不一致 (期待=0x%02X, 取得=0x%02X)\n",
               CHIP_ID_EXPECTED, chip_id);
        return false;
    }
    printf("BNO055: チップID確認OK (0x%02X)\n", chip_id);

    // CONFIGモード → リセット
    write_reg(REG_OPR_MODE, OPR_CONFIG);
    sleep_ms(25);
    write_reg(REG_SYS_TRIGGER, 0x20);
    sleep_ms(700);

    // リセット後、チップIDが読めるまで待機
    chip_id = 0;
    for (int i = 0; i < 10; i++) {
        read_regs(REG_CHIP_ID, &chip_id, 1);
        if (chip_id == CHIP_ID_EXPECTED) break;
        sleep_ms(100);
    }
    if (chip_id != CHIP_ID_EXPECTED) {
        printf("BNO055: リセット後にチップIDが読めません\n");
        return false;
    }

    // 通常電源・ページ0・外部クロック
    write_reg(REG_PWR_MODE, 0x00);
    sleep_ms(10);
    write_reg(REG_PAGE_ID, 0x00);
    write_reg(REG_SYS_TRIGGER, 0x80);
    sleep_ms(10);

    // NDOFモード (9軸フュージョン)
    write_reg(REG_OPR_MODE, OPR_NDOF);
    sleep_ms(20);

    printf("BNO055: 初期化完了 (NDOFモード)\n");
    return true;
}

bool bno055_read_euler(bno055_vec3_t *euler) {
    // 1/16度単位
    return read_vec3(REG_EUL_YAW, 16.0f, euler);
}

bool bno055_read_linear_accel(bno055_vec3_t *accel) {
    // 1/100 m/s^2単位
    return read_vec3(REG_LIA_X, 100.0f, accel);
}
