Revisions
---------

2025.2.20

- Rename LifFileFormat to LifFileType (breaking).
- Rename LifFile.format to LifFile.type (breaking).

2025.2.10

- Support case-sensitive file systems.
- Support OMETiffBlock, AiviaTiffBlock, and other memory blocks.
- Remove LifImageSeries.items and paths methods (breaking).
- Deprecate LifImage.xml_element_smd.
- Fix LifImage.parent_image and child_images properties for XML files.
- Work around reading float16 blocks from uint16 OME-TIFF files.

2025.2.8

- Support LIFEXT files.
- Remove asrgb parameter from LifImage.asarray (breaking).
- Do not apply BGR correction when using memory block frames.
- Avoid copying single frame to output array.
- Add LifImage.parent_image and child_images properties.
- Add LifImageSeries.find method.

2025.2.6

- Support XLEF and XLCF files.
- Rename LifFile.series property to images (breaking).
- Rename imread series argument to image (breaking).
- Remove LifImage.index property (breaking).
- Add parent and children properties to LifFile.
- Improve detection of XML codecs.
- Do not keep XML files open.

2025.2.5

- Support XLIF files.
- Revise LifMemoryBlock (breaking).
- Replace LifImage.is_lof property with format (breaking).
- Require imagecodecs for decoding TIF, JPEG, PNG, and BMP frames.

2025.2.2

- Add LifFlimImage class.
- Derive LifImage and LifFlimImage from LifImageABC.
- Rename LifImage.guid property to uuid (breaking).
- Add LifFile.uuid property.

2025.1.31

- Support LOF files.
- Make LifFile.xml_header a function (breaking).

2025.1.30

- Remove LifFile.flim_rawdata (breaking).
- Add index, guid, and xml_element_smd properties to LifImage.

2025.1.26

- Fix image coordinate values.
- Prompt for file name if main is called without arguments.

2025.1.25

- Initial alpha release.
