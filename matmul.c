void matmul_naive (const double *a, const double *b, double *c,
                   const int m, const int n, const int p,
                   const int lda, const int ldb, const int ldc) {
  for (int i = 0; i < m; i++) {
    for (int j = 0; j < p; j++) {
      double sum = 0.0;
      for (int k = 0; k < n; k++) {
        sum += a[i + lda * k] * b[k + ldb * j];
      }
      c[i + ldc * j] += sum;
    }
  }
}
