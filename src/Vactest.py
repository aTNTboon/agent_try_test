import numpy as np



def get_dot(vec_a,vec_b)->int:
    if(len(vec_a)==len(vec_b)):
        doc_sum=0
        for a,b in zip(vec_a,vec_b):
            doc_sum+=a*b
        return doc_sum
    raise Exception("向量无法对齐")


def get_norm(vec_a):
    sum_square=0
    for v in vec_a:
        sum_square+=v*v

    return np.sqrt(sum_square)


def cosine_similarity(vec_a,vec_b):
    result =get_dot(vec_a,vec_b)/(get_norm(vec_a)*get_norm(vec_b))
    print(result)

if __name__ == "__main__":
    vec_a = [0.5,0.5]
    vec_b=[0.6,-0.1]
    cosine_similarity(vec_a,vec_b)