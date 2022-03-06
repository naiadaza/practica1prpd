from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore, Lock
from multiprocessing import current_process
from multiprocessing import Value, Array
from time import sleep
from random import random,randint

N = 5
K = 10
NPROD = 3 #numero de productores
NCONS = 1 #numero de consumidores

def delay(factor = 3):
    sleep(random()/factor)

def add_data(storage, index, data, mutex):
    mutex.acquire()
    try:
        storage[index.value] = data
        delay(6)
        index.value = index.value + 1
    finally:
        mutex.release()

def get_data(storage, index, mutex):
    mutex.acquire()
    try:
        data = storage[0]
        index.value = index.value - 1
        delay(6)
        for i in range(index.value):
            storage[i] = storage[i + 1]
        storage[index.value] = -1
    finally:
        mutex.release()
    return data

#función productor
def producer(storage_lista, index_lista, empty_lista, non_empty_lista, mutex_lista):
    i = 0
    for j in range(N):
        print (f"producer {current_process().name} produciendo")
        delay(6)
        empty_lista.acquire()
        i = i + randint(0,15) #datos random
        add_data(storage_lista, index_lista, i, mutex_lista)
        non_empty_lista.release()
        print (f"producer {current_process().name} almacenado {j}")
    empty_lista.acquire()
    add_data (storage_lista,index_lista, -1,mutex_lista) #para saber el final
    non_empty_lista.release()

#Lista buleana para ver si quedan en cada uno de los NPROD 
def productoresRest (storage_lista,index_lista):
    result =[]
    for i in range(NPROD):
        result.append(storage_lista[i][0] != -1)
    return result

#Minimo de una lista, en la que meto como variables dos listas una con los valores minimos y otra con los indices
def minimo(valores,indices):
    minimo_valor=min(valores)
    index=valores.index(minimo_valor)
    minimo_indice=indices[index]
    return minimo_valor , minimo_indice

#Dado el storage develve dos listas valores e indices
def aux(result,storage_lista):
    valores , indices = [] , []
    for i in range(NPROD):
        if result[i]:
            valores.append(storage_lista[i][0])
            indices.append(i)
    return valores , indices

def minimoDeTodos(storage_lista, index_lista,mutex_lista):
    result= productoresRest(storage_lista,index_lista)
    numeros , indices = aux(result,storage_lista)
    if len(numeros)!=0: #queda alguno por añadir
       minimo_valor , minimo_indice = minimo(numeros,indices)
       get_data(storage_lista[minimo_indice], index_lista[minimo_indice], mutex_lista[minimo_indice])
    return minimo_valor , minimo_indice

def hayproductores(storage_lst,index_lst):
    b = productoresRest(storage_lst,index_lst)
    for i in range(NPROD): #Hay alguno que no sea False (no vacio)
        if b[i]:
           return True
    return False
 
#función consumidor
def consumer(lista_ordenada,storage_lst, index_lst, empty_lst, non_empty_lst, mutex_lst):
    for i in range(NPROD):
        non_empty_lst[i].acquire()
    i=0
    while hayproductores(storage_lst,index_lst): #Queda alguno
        minimo_valor , minimo_indice =minimoDeTodos(storage_lst, index_lst,mutex_lst) #cogemos el minimo
        print (f"consumer {current_process().name} desalmacenando")
        lista_ordenada[i]=minimo_valor  #lo añadimos a la lista final
        empty_lst[minimo_indice].release()
        non_empty_lst[minimo_indice].acquire()
        print(f"consumer {current_process().name} consumiendo {minimo_valor}")
        i+=1

def main():
    lista_ordenada= Array('i',N*NPROD)
    storage_lista= [Array('i',K) for i in range (NPROD)]
    index_lista = [Value('i', 0) for i in range (NPROD)]
    non_empty_lista = [Semaphore(0) for i in range(NPROD)]
    empty_lista = [BoundedSemaphore(K) for i in range(NPROD)]
    mutex_lista = [Lock() for i in range(NPROD)]

    prodlst = [ Process(target=producer,
                        name=f'prod_{i}',
                        args=(storage_lista[i], index_lista[i], empty_lista[i], non_empty_lista[i], mutex_lista[i]))for i in range (NPROD)] 
              
    conslst = [ Process(target=consumer,
                      name=f"cons_{i}",
                      args=(lista_ordenada,storage_lista, index_lista, empty_lista, non_empty_lista, mutex_lista)) for i in range (NCONS)] 
                
    for p in prodlst + conslst:
        p.start()

    for p in prodlst + conslst:
        p.join()

    print(lista_ordenada[:])

if __name__ == '__main__':
    main()
