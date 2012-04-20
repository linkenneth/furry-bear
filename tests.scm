;;; Test Cases for the Scheme Project 

;; To run all tests:
;;     python3 scheme_test.py tests.scm
;;


;; The following should work for the initial files.

3
; expect 3

-123
; expect -123

1.25
; expect 1.25

#t
; expect #t

#f
; expect #f

)
; expect Error


;; In the following sections, you should provide test cases, so that by 
;; running 
;;     python3 scheme_test.py tests.scm
;; you can test the portions of the project you've completed.  In fact, 
;; you might consider writing these tests BEFORE tackling the associated
;; problem!

; Problem 1  (the reader)
;   Initially, the project skeleton simply reads and prints the expressions
;   entered.  Later on, it starts evaluating them.  You may therefore need
;   to modify the tests you initially provide for this section when you get
;   to later sections.  For example, initially, entering the symbol x will
;   simply cause the evaluator to print "x" rather than attempting to evaluate
;   it (and getting an error).  Therefore, you may later have to modify
;   x to (e.g.) 'x

(car '(3 4))
; expect 3

(cdr '(3 4))
; expect 4

(car (car '((3 . 4) (5 . 6))))
; expect 3

(car (cdr '((3 . 4) (5 . 6))))
; expect 5

'(3 4 . 5)
; expect (3 4 . 5)

'(3 . 4 5)
; expect Error

'()
; expect ()

'(.)
; expect Error

'( . 4)
; expect Error

'(#t . #f)
; expect Error

'(#t #f #t #f)
; expect (#t #f #t #f)


; Problem 2 (primitive function calls)

; YOUR TEST CASES HERE



; Problem A3 and B3 (symbol evaluation and simple defines)

; YOUR TEST CASES HERE


; Problem A4, B4, A5, B5, and 6 (calls on user-defined functions)

; YOUR TEST CASES HERE


; Problem 7 (set!)

; YOUR TEST CASES HERE


; Problem A8 (if, and)

; YOUR TEST CASES HERE


; Problem B8 (cond, or)

; YOUR TEST CASES HERE


; Problem 9 (let)

; YOUR TEST CASES HERE


; Extra Credit 1 (let*)

; YOUR TEST CASES HERE


; Extra Credit 2 (case)

; YOUR TEST CASES HERE


; Problem A10

;; The subsequence of list S for which F outputs a true value (i.e., one
;; other than #f), computed destructively
(define (filter! f s)
   ; *** YOUR CODE HERE ***
)

(define (big x) (> x 5))

(define ints (list 1 10 3 8 4 7))
(define ints1 (cdr ints))

(define filtered_ints (filter! big ints))
filtered_ints
; expect (10 8 7)
(eq? filtered_ints ints1)
; expect #t


; Problem A11.

;; The number of ways to change TOTAL with DENOMS
;; At most MAX-COINS total coins can be used.
(define (count_change total denoms max-coins)
  ; *** YOUR CODE HERE ***
)

(define us_coins '(50 25 10 5 1))
(count_change 20 us_coins 18)
; expect 8

; Problem B10

;; Reverse list L destructively, creating no new pairs.  May modify the 
;; cdrs of the items in list L.
(define (reverse! L)
   ; *** YOUR CODE HERE ***
)

(define L (list 1 2 3 4))
(define LR (reverse! L))
LR
; expect (4 3 2 1)

(eq? L (list-tail LR 3))
; expect #t

; Problem B11

;; The number of ways to partition TOTAL, where 
;; each partition must be at most MAX_VALUE
(define (count-partitions total max-value)
  ; *** YOUR CODE HERE ***
)

(count-partitions 5 3)
; expect 5
; Note: The 5 partitions are [[3 2] [3 1 1] [2 2 1] [2 1 1 1] [1 1 1 1 1]]

; Problem 12

;; A list of all ways to partition TOTAL, where  each partition must 
;; be at most MAX_VALUE and there are at most MAX_PIECES partitions.
(define (list-partitions total max-pieces max-value)
  ; *** YOUR CODE HERE ***
)

(list-partitions 5 2 4)
; expect ((4 1) (3 2))
(list-partitions 7 3 5)
; expect ((5 2) (5 1 1) (4 3) (4 2 1) (3 3 1) (3 2 2))



