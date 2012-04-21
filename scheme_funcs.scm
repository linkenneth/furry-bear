(define (filter! pred L)
                (cond ((null? (cdr L)) (car L))
                        ((not (pred (car L))) (set! L (filter! pred (cdr L)))))
                         L)

(define x '(2 3 4 5 6 7))