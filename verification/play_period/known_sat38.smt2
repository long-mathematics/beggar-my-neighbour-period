(declare-fun gap_0 () Int)
(declare-fun gap_1 () Int)
(declare-fun gap_2 () Int)
(declare-fun gap_3 () Int)
(declare-fun gap_4 () Int)
(declare-fun gap_5 () Int)
(declare-fun gap_6 () Int)
(declare-fun gap_7 () Int)
(declare-fun gap_8 () Int)
(declare-fun gap_9 () Int)
(declare-fun gap_10 () Int)
(declare-fun gap_11 () Int)
(declare-fun gap_12 () Int)
(declare-fun gap_13 () Int)
(declare-fun gap_14 () Int)
(declare-fun gap_15 () Int)
(declare-fun gap_16 () Int)
(declare-fun gap_17 () Int)
(declare-fun rank_0 () Int)
(declare-fun rank_1 () Int)
(declare-fun rank_2 () Int)
(declare-fun rank_3 () Int)
(assert (>= gap_0 0))
(assert (>= gap_1 0))
(assert (>= gap_2 0))
(assert (>= gap_3 0))
(assert (>= gap_4 0))
(assert (>= gap_5 0))
(assert (>= gap_6 0))
(assert (>= gap_7 0))
(assert (>= gap_8 0))
(assert (>= gap_9 0))
(assert (>= gap_10 0))
(assert (>= gap_11 0))
(assert (>= gap_12 0))
(assert (>= gap_13 0))
(assert (>= gap_14 0))
(assert (>= gap_15 0))
(assert (>= gap_16 0))
(assert (>= gap_17 0))
(assert (= (+ gap_0
      gap_1
      gap_2
      gap_3
      gap_4
      gap_5
      gap_6
      gap_7
      gap_8
      gap_9
      gap_10
      gap_11
      gap_12
      gap_13
      gap_14
      gap_15
      gap_16
      gap_17)
   36))
(assert (and (>= rank_0 1) (<= rank_0 4)))
(assert (and (>= rank_1 1) (<= rank_1 4)))
(assert (and (>= rank_2 1) (<= rank_2 4)))
(assert (and (>= rank_3 1) (<= rank_3 4)))
(assert (= (+ (ite (= rank_0 1) 4 0)
      (ite (= rank_1 1) 4 0)
      (ite (= rank_2 1) 4 0)
      (ite (= rank_3 1) 4 0))
   4))
(assert (= (+ (ite (= rank_0 2) 4 0)
      (ite (= rank_1 2) 4 0)
      (ite (= rank_2 2) 4 0)
      (ite (= rank_3 2) 4 0))
   4))
(assert (= (+ (ite (= rank_0 3) 4 0)
      (ite (= rank_1 3) 4 0)
      (ite (= rank_2 3) 4 0)
      (ite (= rank_3 3) 4 0))
   4))
(assert (= (+ (ite (= rank_0 4) 4 0)
      (ite (= rank_1 4) 4 0)
      (ite (= rank_2 4) 4 0)
      (ite (= rank_3 4) 4 0))
   4))
(assert (>= gap_10 (+ gap_0 0)))
(assert (>= (- gap_10 (+ gap_0 0)) 0))
(assert (< (- gap_10 (+ gap_0 0)) rank_0))
(assert (>= gap_1 rank_3))
(assert (>= gap_11 (+ (- gap_1 rank_3) 1)))
(assert (>= (- gap_11 (+ (- gap_1 rank_3) 1)) 0))
(assert (< (- gap_11 (+ (- gap_1 rank_3) 1)) rank_1))
(assert (>= gap_2 rank_0))
(assert (>= (- gap_2 rank_0) (+ gap_12 0)))
(assert (>= (- (- gap_2 rank_0) (+ gap_12 0)) rank_3))
(assert (let ((a!1 (+ (- (- (- gap_2 rank_0) (+ gap_12 0)) rank_3) 1)))
  (>= gap_13 a!1)))
(assert (let ((a!1 (+ (- (- (- gap_2 rank_0) (+ gap_12 0)) rank_3) 1)))
  (>= (- gap_13 a!1) 0)))
(assert (let ((a!1 (+ (- (- (- gap_2 rank_0) (+ gap_12 0)) rank_3) 1)))
  (< (- gap_13 a!1) rank_2)))
(assert (>= gap_3 0))
(assert (< gap_3 rank_1))
(assert (>= gap_14 0))
(assert (< gap_14 rank_2))
(assert (>= gap_4 0))
(assert (< gap_4 rank_0))
(assert (>= gap_15 rank_1))
(assert (>= gap_5 (+ (- gap_15 rank_1) 1)))
(assert (>= (- gap_5 (+ (- gap_15 rank_1) 1)) rank_3))
(assert (let ((a!1 (- (- gap_5 (+ (- gap_15 rank_1) 1)) rank_3)))
  (>= gap_16 (+ a!1 1))))
(assert (let ((a!1 (- (- gap_5 (+ (- gap_15 rank_1) 1)) rank_3)))
  (>= (- gap_16 (+ a!1 1)) rank_2)))
(assert (= gap_6 gap_0))
(assert (= gap_7 gap_1))
(assert (= gap_8 gap_2))
(assert (let ((a!1 (* 2 (- (- (- gap_2 rank_0) (+ gap_12 0)) rank_3))))
  (= (+ gap_9 a!1 1) gap_3)))
(assert (let ((a!1 (+ (- (- (- gap_2 rank_0) (+ gap_12 0)) rank_3) 1)))
  (= (- gap_13 a!1) gap_4)))
(assert (= gap_3 gap_5))
(assert (= gap_14 gap_6))
(assert (= gap_4 gap_7))
(assert (let ((a!1 (- (- gap_5 (+ (- gap_15 rank_1) 1)) rank_3)))
  (= (+ rank_1 (* 2 a!1) 1) gap_8)))
(assert (= rank_2 gap_9))
(assert (let ((a!1 (- (- gap_5 (+ (- gap_15 rank_1) 1)) rank_3)))
  (= (- (- gap_16 (+ a!1 1)) rank_2) gap_10)))
(assert (= (+ gap_17 (* 2 gap_0) 0) gap_11))
(assert (= (- gap_10 (+ gap_0 0)) gap_12))
(assert (= (+ rank_3 (* 2 (- gap_1 rank_3)) 1) gap_13))
(assert (= (- gap_11 (+ (- gap_1 rank_3) 1)) gap_14))
(assert (= (+ rank_0 (* 2 gap_12) 0) gap_15))
(assert (= (+ rank_3 (* 2 (- gap_15 rank_1)) 1) gap_16))
(assert (= rank_3 gap_17))
(assert (let ((a!1 (* 2 (- (- (- gap_2 rank_0) (+ gap_12 0)) rank_3)))
      (a!2 (+ (- (- (- gap_2 rank_0) (+ gap_12 0)) rank_3) 1))
      (a!3 (- (- gap_5 (+ (- gap_15 rank_1) 1)) rank_3)))
(let ((a!4 (+ 0
              2
              (* 2 gap_0)
              0
              (- gap_10 (+ gap_0 0))
              rank_3
              2
              (* 2 (- gap_1 rank_3))
              1
              (- gap_11 (+ (- gap_1 rank_3) 1))
              rank_0
              1
              (* 2 gap_12)
              0
              rank_3
              5
              a!1
              1
              (- gap_13 a!2)
              gap_3
              gap_14
              gap_4
              rank_1
              1
              (* 2 (- gap_15 rank_1))
              1
              rank_3
              1
              (* 2 a!3)
              1
              rank_2)))
  (<= a!4 38))))

(check-sat)
