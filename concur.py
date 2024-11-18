def get_tickers_from_csv(with_dots=False):

    import csv
    tickers = []
    with open('valid_tickers.csv', newline='') as csvfile:

        spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
        flag = True
        for row in spamreader:
            if flag:
                flag = False
                continue
            for elem in row:
                if with_dots or '.' not in elem:
                    tickers.append(elem[2:-2])
                break
    return sorted(tickers)

