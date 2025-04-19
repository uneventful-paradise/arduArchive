/*******************************************************************************
 * JPEGDEC related function
 *
 * Dependent libraries:
 * JPEGDEC: https://github.com/bitbank2/JPEGDEC.git
 ******************************************************************************/
#ifndef _JPEGFUNC_H_
#define _JPEGFUNC_H_

#include <JPEGDEC.h>
#include "SdFat.h"
extern SdFat sd;

static JPEGDEC _jpeg;
static SdFile _f;
static int _x, _y, _x_bound, _y_bound;

static void *jpegOpenFile(const char *szFilename, int32_t *pFileSize) {
  // Open the file in read-only mode using SdFat.
  // If the file fails to open, return nullptr and set the file size to 0.
  if (!_f.open(szFilename, O_READ)) {
    *pFileSize = 0;
    // Serial.printf("ERROR: JPEGDEC cannot open file for drawing.\n");
    return nullptr;
  }
  *pFileSize = _f.fileSize();
  return &_f;
}

static void jpegCloseFile(void *pHandle) {
  // Serial.println("jpegCloseFile");
  SdFile *f = static_cast<SdFile *>(pHandle);
  f->close();
}

static int32_t jpegReadFile(JPEGFILE *pFile, uint8_t *pBuf, int32_t iLen) {
  // Serial.printf("jpegReadFile, iLen: %d\n", iLen);
  SdFile *f = static_cast<SdFile *>(pFile->fHandle);
  // SdFile::read returns the number of bytes read.
  int16_t r = f->read(pBuf, iLen);
  return r;
}

static int32_t jpegSeekFile(JPEGFILE *pFile, int32_t iPosition) {
  SdFile *f = static_cast<SdFile *>(pFile->fHandle);
  // Use seekSet instead of seek for SdFat.
  f->seekSet(iPosition);
  return iPosition;
}

static void jpegDraw(
  const char *filename, JPEG_DRAW_CALLBACK *jpegDrawCallback, bool useBigEndian,
  int x, int y, int widthLimit, int heightLimit) {
  _x = x;
  _y = y;
  _x_bound = _x + widthLimit - 1;
  _y_bound = _y + heightLimit - 1;

  _jpeg.open(filename, jpegOpenFile, jpegCloseFile, jpegReadFile, jpegSeekFile, jpegDrawCallback);

  // scale to fit height
  int _scale;
  int iMaxMCUs;
  float ratio = (float)_jpeg.getHeight() / heightLimit;
  if (ratio <= 1) {
    _scale = 0;
    iMaxMCUs = widthLimit / 16;
  } else if (ratio <= 2) {
    _scale = JPEG_SCALE_HALF;
    iMaxMCUs = widthLimit / 8;
  } else if (ratio <= 4) {
    _scale = JPEG_SCALE_QUARTER;
    iMaxMCUs = widthLimit / 4;
  } else {
    _scale = JPEG_SCALE_EIGHTH;
    iMaxMCUs = widthLimit / 2;
  }
  _jpeg.setMaxOutputSize(iMaxMCUs);
  if (useBigEndian) {
    _jpeg.setPixelType(RGB565_BIG_ENDIAN);
  }
  _jpeg.decode(x, y, _scale);
  _jpeg.close();
}

#endif  // _JPEGFUNC_H_