us_coins = [50, 25, 10, 5, 1]

def count_change(amount, coins, max_coins):
    if not coins or amount < 0:
        return 0
    elif amount == 0:
        return 1
    elif max_coins == 0:
        return 0
    else:
        return count_change(amount - coins[0], coins, max_coins - 1) + count_change(amount, coins[1:], max_coins)
