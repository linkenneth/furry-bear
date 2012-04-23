(define x 3)
(define y 4)
(define z 5)

(define L (list 1 2 3 4 5))

(define (reverse! L)
  (define (reverse1 L first sofar)
    (cond ((null? (cdr L)) L)
	  ((not (= (length L) 1)) (reverse1 (cdr L) first sofar))
	  (else (set-cdr! (reverse1 (cdr L) first sofar) '(car L)) (reverse1 (cdr L) first L))))
  (reverse1 L (car L) '())
)

(define (reverse1! L)
  (cond ((null? (cdr L)) L)
	(else (set-cdr! (list-tail (reverse1! (cdr L)) (- (length L) 1)) (list (car L))) L)))


(define (count_change total denoms max-coins)
  (cond ((or (null? denoms) (< total 0)) 0)
	((= total 0) 1)
	((= max-coins 0) 0)
	(else (+ (count_change (- total (car denoms)) denoms (- max-coins 1)) (count_change total (cdr denoms) max-coins)))))

(define us_coins '(50 25 10 5 1))