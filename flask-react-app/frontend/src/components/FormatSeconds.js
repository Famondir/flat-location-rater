export const formatSeconds = (seconds) => {
    if (seconds !== 0) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours} h ${minutes} min`;
    }
    
    return NaN;
};