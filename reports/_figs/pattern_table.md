# Pattern complexity vs steerability (CIFAR-10)

`support` = nonzero entries in the [3,32,32] pattern (complexity proxy). `chance` = support/3072 = mass_frac a random perturbation puts on the support. Verdict: **drawn** iff support_cos clearly > 0 AND mass_frac > chance at clean acc > 0.5.

| pattern | support | chance | mechanism | clean_acc | best support_cos | best mass_frac | verdict |
|---------|--------:|-------:|-----------|----------:|-----------------:|---------------:|---------|
| cross (full) | 720 | 0.234 | AdversarialSinkLoss (align+sink+robust) | 0.611 | +0.009 | 0.279 | not drawn |
| cross (full) | 720 | 0.234 | alignment fine-tune a=4 | 0.713 | -0.002 | 0.289 | not drawn |
| small_cross (8x8) | 84 | 0.027 | CrossTrapLoss (targeted UAP) | 0.107 | +0.020 | 0.035 | collapsed |
| corner_square 4x4 | 48 | 0.016 | BadNet poison | 0.642 | +0.037 | 0.019 | not drawn |
| corner_square 4x4 | 48 | 0.016 | BadNet + L2 orthogonal AT | 0.466 | +0.018 | 0.011 | not drawn |
| corner_square 4x4 | 48 | 0.016 | masked-AT confinement | 0.532 | -0.003 | 0.011 | not drawn |
