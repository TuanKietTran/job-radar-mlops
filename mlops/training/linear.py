'''Small linear-algebra helpers for ordinary least squares.

Standard library only. Fits y = intercept + sum w_i * (x_i - mean_i) / std_i
by solving the ridge-stabilised normal equations with Gaussian
elimination and partial pivoting.
'''


def mean(values):
    '''Return the arithmetic mean of a non-empty list.'''
    return sum(values) / len(values)


def solve_linear(matrix, vector):
    '''Solve matrix * x = vector by Gaussian elimination.'''
    size = len(vector)
    augmented = [list(matrix[i]) + [vector[i]] for i in range(size)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError('singular matrix')
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        for row in range(column + 1, size):
            factor = augmented[row][column] / augmented[column][column]
            for item in range(column, size + 1):
                augmented[row][item] -= factor * augmented[column][item]
    solution = [0.0] * size
    for row in range(size - 1, -1, -1):
        total = augmented[row][size] - sum(augmented[row][item] * solution[item] for item in range(row + 1, size))
        solution[row] = total / augmented[row][row]
    return solution


def fit_linear(rows, targets, ridge=1e-8):
    '''Fit a linear model; return weights, means, stds and intercept.'''
    if not rows:
        raise ValueError('no training rows')
    n_features = len(rows[0])
    means = [mean([row[j] for row in rows]) for j in range(n_features)]
    stds = []
    for j in range(n_features):
        column = [row[j] for row in rows]
        variance = sum((value - means[j]) ** 2 for value in column) / len(column)
        std = variance ** 0.5
        stds.append(std if std > 1e-12 else 1.0)
    standardised = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in rows]
    y_mean = mean(targets)
    centred = [target - y_mean for target in targets]
    matrix = [[0.0] * n_features for _ in range(n_features)]
    vector = [0.0] * n_features
    for row, target in zip(standardised, centred):
        for i in range(n_features):
            vector[i] += row[i] * target
            for j in range(n_features):
                matrix[i][j] += row[i] * row[j]
    for i in range(n_features):
        matrix[i][i] += ridge
    weights = solve_linear(matrix, vector)
    return {'weights': weights, 'means': means, 'stds': stds, 'intercept': y_mean}


def predict_linear(model, row):
    '''Predict with a fitted linear model dict.'''
    total = model['intercept']
    for weight, mean_value, std, value in zip(model['weights'], model['means'], model['stds'], row):
        total += weight * (value - mean_value) / std
    return total
