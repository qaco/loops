#include <stdio.h>
#include <immintrin.h>

#define I 512
#define J 512
#define K 512

void matrix_multiply(float a[I][K], float b[K][J], float result[I][J]) {
  for (int i = 0; i < I; ++i) {
    for (int j = 0; j < J; ++j) {
      __m128 result_row = _mm_setzero_ps();
      for (int k = 0; k < K; k += 4) {
        __m128 a_row = _mm_loadu_ps(&a[i][k]);
        __m128 b_col = _mm_loadu_ps(&b[k][j]);
        result_row = _mm_add_ps(result_row, _mm_mul_ps(a_row, b_col));
      }
      _mm_storeu_ps(&result[i][j], result_row);
    }
  }
}

int main() {

  float a[I][K];
  float b[K][J];
  float result[I][J];

  matrix_multiply(a, b, result);
  
  /* float a[4][4] = {{1, 2, 3, 4}, {5, 6, 7, 8}, {9, 10, 11, 12}, {13, 14, 15, 16}}; */
  /* float b[4][4] = {{1, 0, 0, 0}, {0, 1, 0, 0}, {0, 0, 1, 0}, {0, 0, 0, 1}}; */
  /* float result[4][4]; */

  /* matrix_multiply(a, b, result); */

  /* printf("Result:\n"); */
  /* for (int i = 0; i < 4; ++i) { */
  /*   for (int j = 0; j < 4; ++j) { */
  /*     printf("%.2f ", result[i][j]); */
  /*   } */
  /*   printf("\n"); */
  /* } */

  return 0;
}
