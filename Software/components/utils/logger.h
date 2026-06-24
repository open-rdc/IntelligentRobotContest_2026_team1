#ifndef LOGGER_H
#define LOGGER_H

// 100ms周期でセンサ値とモータ出力をシリアルモニタに出力する
// mainループ内で毎サイクル呼び出しても、100ms経過するまでは何も出力しない
void logger_update(void);

#endif // LOGGER_H
