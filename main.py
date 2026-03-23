
# region imports
from AlgorithmImports import *
# endregion
class Tesis(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2020, 1, 1)
        self.set_end_date(2024, 1, 2)
        self.set_cash(100000)
        self.activo = self.add_equity("AAPL", Resolution.DAILY)
        self.mediaMovilRapida = self.sma(self.activo.symbol, 50, Resolution.DAILY)
        self.mediaMovilLenta = self.sma(self.activo.symbol, 200, Resolution.DAILY)
        #Graficar Precios y Medias Móviles
        self.nombreGrafico = f"Gráfico de {self.activo.symbol.value}"
        graficoVela = Chart(self.nombreGrafico)
        graficoVela.add_series(Series("Precio", SeriesType.CANDLE, 0))
        graficoVela.add_series(Series("Media Móvil Rápida", SeriesType.LINE, '$', Color.ORANGE))
        graficoVela.add_series(Series("Media Móvil Lenta", SeriesType.LINE, '$', Color.BLUE))
        self.add_chart(graficoVela)
        #Crear columnas de archivo final a analizar
        self.datos_csv = "Fecha,Precio,MediaRapida,MediaLenta,CapitalTotal\n"
    def on_data(self, data: Slice):
        if not self.mediaMovilRapida.is_ready or not self.mediaMovilLenta.is_ready:
            return
            
        compraVenta, mmRapida, mmLenta = self.CompararMediasMoviles()
        if not self.portfolio.invested and compraVenta == 1:
            self.set_holdings(self.activo.symbol, 1)
        elif self.portfolio.invested and compraVenta == -1:
            self.set_holdings(self.activo.symbol, 0)
     
        fecha = self.time.strftime("%Y-%m-%d")
        precio = self.securities[self.activo].close
        rapida = round(mmRapida, 2)
        lenta = round(mmLenta, 2)
        capital = round(self.portfolio.total_portfolio_value, 2)
    
        # Añadir la nueva fila al texto
        self.datos_csv += f"{fecha},{precio},{rapida},{lenta},{capital}\n"
        if self.time.date() == self.end_date.date():
            self.debug("Se vende todo lo que se tiene")
            self.liquidate()
    def CompararMediasMoviles(self):
        rapida = self.mediaMovilRapida.current.value
        lenta = self.mediaMovilLenta.current.value
        fechaActual = self.time.strftime("%Y-%m-%d")
        self.Graficar(rapida, lenta)
        if rapida > lenta:
            if not self.portfolio.invested:
                self.debug(f"La media móvil rápida superó a la lenta en: {fechaActual}. Se va a comprar a {self.securities[self.activo].price}. Media Rápida: {rapida:.2f} | Media Lenta: {lenta:.2f}")
            return 1, rapida, lenta            #Señar para comprar (el precio va a subir)
        elif rapida < lenta:
            if self.portfolio.invested: 
                self.debug(f"La media móvil rápida cayó bajo la lenta en: {fechaActual}. Se va a vender a {self.securities[self.activo].price}. Media Rápida: {rapida:.2f} | Media Lenta: {lenta:.2f}")
            return -1, rapida, lenta           #Señal para vender (el precio va a bajar)
        else:
            return 0, rapida, lenta            #Señal de no hacer nada si está iguales por incertidumbre
    def Graficar(self, rapida, lenta):
        self.plot(self.nombreGrafico, "Precio", self.securities[self.activo.symbol].price)
        self.plot(self.nombreGrafico, "Media Móvil Rápida", rapida)
        self.plot(self.nombreGrafico, "Media Móvil Lenta", lenta)
    def on_end_of_algorithm(self):
        self.object_store.save(f"{self.activo.symbol}.csv", self.datos_csv)
        self.debug("Archivo CSV guardado en ObjectStore.")
