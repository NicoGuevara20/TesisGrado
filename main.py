# region imports
from AlgorithmImports import *
# endregion

class Tesis(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2020, 1, 1)
        self.set_end_date(2024, 1, 2)
        self.set_cash(100000)

        self.activo = self.add_equity("GLD", Resolution.DAILY)
        #self.activo = self.add_crypto("BTCUSD", Resolution.DAILY)

        #Configuración de medias móviles para largo plazo
        self.mediaMovilRapida = self.sma(self.activo.symbol, 50, Resolution.DAILY)
        self.mediaMovilLenta = self.sma(self.activo.symbol, 200, Resolution.DAILY)

        #Configuración de medias móviles para corto plazo
        #self.mediaMovilRapida = self.sma(self.activo.symbol, 20, Resolution.DAILY)
        #self.mediaMovilLenta = self.sma(self.activo.symbol, 50, Resolution.DAILY)

        self.listaRapida = RollingWindow[float](2)
        self.listaLenta = RollingWindow[float](2)

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
        elif compraVenta == 0:
            return

        self.EscribirArchivoCSV(mmRapida, mmLenta)
     
        if self.time.date() == self.end_date.date():
            self.debug("Se vende todo lo que se tiene")
            self.liquidate()

    def CompararMediasMoviles(self):
        self.listaRapida.add(self.mediaMovilRapida.current.value)
        self.listaLenta.add(self.mediaMovilLenta.current.value)
        self.fechaActual = self.time.strftime("%Y-%m-%d")

        if not self.listaRapida.is_ready and not self.listaLenta.is_ready:
            return 0, 0, 0
        else:
            rapidaHoy = self.listaRapida[0]
            rapidaAyer = self.listaRapida[1]
            lentaHoy = self.listaLenta[0]
            lentaAyer = self.listaLenta[1]
        
        self.Graficar(rapidaAyer, lentaAyer)

        if rapidaHoy > lentaHoy and rapidaAyer <= lentaAyer:
            if not self.portfolio.invested:
                self.debug(f"La media móvil rápida superó a la lenta en: {self.fechaActual}. Se va a comprar a {self.securities[self.activo].price}. Media Rápida: {rapidaHoy:.2f} | Media Lenta: {lentaHoy:.2f}")
            return 1, rapidaHoy, lentaHoy            #Señar para comprar (el precio va a subir)
        elif rapidaHoy < lentaHoy and rapidaAyer >= lentaAyer:
            if self.portfolio.invested: 
                self.debug(f"La media móvil rápida cayó bajo la lenta en: {self.fechaActual}. Se va a vender a {self.securities[self.activo].price}. Media Rápida: {rapidaHoy:.2f} | Media Lenta: {lentaHoy:.2f}")
            return -1, rapidaHoy, lentaHoy           #Señal para vender (el precio va a bajar)
        else:
            return 0, rapidaHoy, lentaHoy            #Señal de no hacer nada si está iguales por incertidumbre

    def Graficar(self, rapida, lenta):
        self.plot(self.nombreGrafico, "Precio", self.securities[self.activo.symbol].price)
        self.plot(self.nombreGrafico, "Media Móvil Rápida", rapida)
        self.plot(self.nombreGrafico, "Media Móvil Lenta", lenta)

    def EscribirArchivoCSV(self, mmRapida, mmLenta):
        fecha = self.time.strftime("%Y-%m-%d")
        precio = self.securities[self.activo].close
        rapida = round(mmRapida, 2)
        lenta = round(mmLenta, 2)
        capital = round(self.portfolio.total_portfolio_value, 2)
        
        #Escribir nueva fila
        self.datos_csv += f"{fecha},{precio},{rapida},{lenta},{capital}\n"

    def on_end_of_algorithm(self):
        self.object_store.save(f"{self.activo.symbol}_{self.fechaActual}.csv", self.datos_csv)
        self.debug("Archivo CSV guardado en ObjectStore.")
