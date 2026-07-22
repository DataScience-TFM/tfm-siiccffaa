# Comparación de técnicas predictivas

## Objetivo

Clasificar si la actividad de una combinación de provincia y tipo de reporte aumentará durante la semana siguiente.

## Técnicas evaluadas

1. Regresión logística: familia lineal probabilística.
2. Árbol de decisión: reglas y particiones no lineales.
3. Random Forest: ensamblado mediante *bagging*.
4. SVM lineal: clasificador de margen máximo.

La clase mayoritaria y la persistencia son baselines y no se contabilizan entre las cuatro técnicas.

## Procedimiento paso a paso

1. Validar el esquema y la continuidad semanal.
2. Crear variables usando únicamente información anterior al objetivo.
3. Reservar el 15 % más reciente como prueba final intocable.
4. Crear tres ventanas temporales expansivas dentro del 85 % anterior para ajustar el umbral.
5. Imputar, estandarizar variables numéricas y codificar categorías mediante *one-hot*.
6. Entrenar las cuatro técnicas con ponderación por desbalance.
7. Elegir para cada modelo el umbral que maximiza F1 en las ventanas de validación.
8. Reentrenar cada técnica con todo el periodo anterior a prueba.
9. Evaluar una sola vez en prueba con precisión, recall, F1, PR-AUC, ROC-AUC y Precision@20.
10. Mantener la regresión logística como modelo operativo por interpretabilidad y calibración.

## Reproducibilidad

Ejecutar `.\run_model.ps1`. Los resultados se escriben en `outputs/model_comparison.csv`, los modelos en `models/` y la documentación visual queda disponible en `/metodologia`.
