class MapService {
  constructor() {
    this.mapCache = new Map()
  }

  // PNG ?•ì‹??ì§€???´ë?ì§€ë¥?ë¡œë“œ?˜ê³  ìº”ë²„?¤ì—???¬ìš©?????ˆëŠ” ?°ì´?°ë¡œ ë³€??
  async loadMapImage(url) {
    if (this.mapCache.has(url)) {
      return this.mapCache.get(url)
    }

    return new Promise((resolve, reject) => {
      const img = new Image()
      img.crossOrigin = 'anonymous'
      
      img.onload = () => {
        const canvas = document.createElement('canvas')
        canvas.width = img.width
        canvas.height = img.height
        const ctx = canvas.getContext('2d')
        ctx.drawImage(img, 0, 0)
        
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
        const mapData = {
          width: img.width,
          height: img.height,
          resolution: 0.05, // ê¸°ë³¸ê°? ?œë²„?ì„œ ë°›ì•„?€????
          origin: { x: 0, y: 0 }, // ê¸°ë³¸ê°? ?œë²„?ì„œ ë°›ì•„?€????
          data: new Uint8Array(img.width * img.height)
        }

        // RGBA ?°ì´?°ë? ê·¸ë ˆ?´ìŠ¤ì¼€?¼ë¡œ ë³€??
        for (let i = 0; i < imageData.data.length; i += 4) {
          const gray = Math.round((imageData.data[i] + imageData.data[i + 1] + imageData.data[i + 2]) / 3)
          mapData.data[i / 4] = gray
        }

        this.mapCache.set(url, mapData)
        resolve(mapData)
      }

      img.onerror = reject
      img.src = url
    })
  }

  // YAML/JSON ?•ì‹??ì§€??ë©”í??°ì´??ë¡œë“œ
  async loadMapMetadata(url) {
    const response = await fetch(url)
    const metadata = await response.json()
    return metadata
  }

  // ì§€???°ì´?°ì? ë©”í??°ì´??ê²°í•©
  async loadMap(imageUrl, metadataUrl) {
    try {
      const [mapData, metadata] = await Promise.all([
        this.loadMapImage(imageUrl),
        this.loadMapMetadata(metadataUrl)
      ])

      return {
        ...mapData,
        resolution: metadata.resolution,
        origin: metadata.origin
      }
    } catch (error) {
      console.error('ì§€??ë¡œë“œ ?¤íŒ¨:', error)
      throw error
    }
  }

  // ?”ë“œ ì¢Œí‘œë¥??½ì? ì¢Œí‘œë¡?ë³€??
  worldToPixel(worldX, worldY, mapData) {
    const pixelX = Math.round((worldX - mapData.origin.x) / mapData.resolution)
    const pixelY = Math.round((worldY - mapData.origin.y) / mapData.resolution)
    return { x: pixelX, y: mapData.height - pixelY } // Yì¶?ë°˜ì „
  }

  // ?½ì? ì¢Œí‘œë¥??”ë“œ ì¢Œí‘œë¡?ë³€??
  pixelToWorld(pixelX, pixelY, mapData) {
    const worldX = pixelX * mapData.resolution + mapData.origin.x
    const worldY = (mapData.height - pixelY) * mapData.resolution + mapData.origin.y
    return { x: worldX, y: worldY }
  }
}

export const mapService = new MapService() 