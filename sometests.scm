(define x 3)
(define y 4)
(define z 5)

(define L (list 1 2 3 4 5))

(define (reverse! L)
  (let loop ((lst lst)
             (acc '()))
    (if (null? lst)
        acc
        (let ((tail (last L)))
          (set-cdr! (cdr L) acc)
          (loop tail lst)))))