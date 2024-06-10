const jwt = require('jsonwebtoken');

module.exports = function(req, res, next) {
    const token = req.headers['authorization'];
    if (!token) {
        return res.status(401).send('Access Denied: No Token Provided!');
    }

    try {
        const tokenWithoutBearer = token.split(' ')[1];
        const verified = jwt.verify(tokenWithoutBearer, process.env.SECRET_KEY);
        req.user = verified;
        next();
    } catch (error) {
        res.status(400).send('Invalid Token');
    }
};
