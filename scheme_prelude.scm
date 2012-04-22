;; Built-in Scheme functions that are defined in Scheme.  
;; These functions are loaded into Scheme to initialize the global
;; environment

(define (caar x) 
  (car (car x)))

(define (cadr x)
  (car (cdr x)))

(define (cdar x)
  (cdr (car x)))

(define (cddr x)
  (cdr (cdr x)))

(define (caaar x)
  (car (car (car x))))

(define (caadr x)
  (car (car (cdr x))))

(define (cadar x)
  (car (cdr (car x))))

(define (caddr x)
  (car (cdr (cdr x))))

(define (cdaar x)
  (cdr (car (car x))))

(define (cdadr x)
  (cdr (car (cdr x))))

(define (cddar x)
  (cdr (cdr (car x))))

(define (cdddr x)
  (cdr (cdr (cdr x))))

(define (list-tail L n)
  (cond ((> n 0) (list-tail (cdr L) (- n 1)))
        ((= n 0) L)
        (else (error |index argument to list-tail may not be negative|))))

(define (list-ref L n)
  (car (list-tail L n)))

(define (assq key L)
  (cond ((null? L) #f)
        ((eq? key (caar L)) (car L))
        (else (assq key (cdr L)))))

(define (assv key L)
  (cond ((null? L) #f)
        ((eqv? key (caar L)) (car L))
        (else (assv key (cdr L)))))


(define (assoc key L)
  (cond ((null? L) #f)
        ((equal? key (caar L)) (car L))
        (else (assoc key (cdr L)))))

(define (memq key L)
  (cond ((null? L) #f)
	((eq? (car L) key) L)
	(else (memq key (cdr L)))))

(define (memv key L)
  (cond ((null? L) #f)
	((eqv? (car L) key) L)
	(else (memv key (cdr L)))))

(define (member key L)
  (cond ((null? L) #f)
	((equal? (car L) key) L)
	(else (member key (cdr L)))))

(define (zero? x)
  (= x 0))

(define (positive? x)
  (> x 0))

(define (negative? x)
  (< x 0))

(define (max L0 . L)
  (define (max1 head rest)
    (cond ((null? rest) head)
          ((< head (car rest)) (max1 (car rest) (cdr rest)))
          (else (max1 head (cdr rest)))))
  (max1 L0 L))

(define (min L0 . L)
  (define (min1 head rest)
    (cond ((null? rest) head)
          ((> head (car rest)) (min1 (car rest) (cdr rest)))
          (else (min1 head (cdr rest)))))
  (min1 L0 L))

(define (abs x)
  (if (< x 0) (- x) x))

(define (reverse L)
  (define (reverse-tail sofar L)
    (if (null? L) sofar
        (reverse-tail (cons (car L) sofar) (cdr L))))
  (reverse-tail '() L))
